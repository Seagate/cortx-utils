#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import errno
import time
import json
import re
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient, ConfigResource
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.message_bus.message_broker import MessageBroker
from cortx.utils.process import SimpleProcess


class KafkaMessageBroker(MessageBroker):
    """ Kafka Server based message broker implementation """

    name = 'kafka'

    # Retention period in Milliseconds
    _default_msg_retention_period = 604800000
    _min_msg_retention_period = 1

    # Maximum retry count
    _max_config_retry_count = 3
    _max_purge_retry_count = 5

    def __init__(self, broker_conf: dict):
        """ Initialize Kafka based Configurations """
        super().__init__(broker_conf)

        kafka_conf = {'bootstrap.servers': self._servers}
        self._admin = AdminClient(kafka_conf)

        self._clients = {'producer': {}, 'consumer': {}}

    def init_client(self, client_type: str, **client_conf: dict):
        """ Obtain Kafka based Producer/Consumer """

        """ Validate and return if client already exists """
        if client_type not in self._clients.keys():
            raise MessageBusError(errno.EINVAL, "Invalid client type %s", \
                client_type)

        if client_conf['client_id'] in self._clients[client_type].keys():
            if self._clients[client_type][client_conf['client_id']] != {}:
                return

        kafka_conf = {}
        kafka_conf['bootstrap.servers'] = self._servers
        kafka_conf['client.id'] = client_conf['client_id']

        if client_type == 'producer':
            producer = Producer(**kafka_conf)
            self._clients[client_type][client_conf['client_id']] = producer

            self._resource = ConfigResource('topic', client_conf['message_type'])
            conf = self._admin.describe_configs([self._resource])
            default_configs = list(conf.values())[0].result()
            for params in ['retention.ms']:
                if params not in default_configs:
                    raise MessageBusError(errno.EINVAL, "Missing required \
                        config parameter %s", params)

            self._saved_retention = int(default_configs['retention.ms']\
                .__dict__['value'])

            # Set retention to default if the value is 1 ms
            self._saved_retention = self._default_msg_retention_period if \
                self._saved_retention == self._min_msg_retention_period else \
                int(default_configs['retention.ms'].__dict__['value'])

        else:
            for entry in ['offset', 'consumer_group', 'message_type', \
                'auto_ack', 'client_id']:
                if entry not in client_conf.keys():
                    raise MessageBusError(errno.EINVAL, "Missing conf entry \
                        %s", entry)

            kafka_conf['enable.auto.commit'] = client_conf['auto_ack']
            kafka_conf['auto.offset.reset'] = client_conf['offset']
            kafka_conf['group.id'] = client_conf['consumer_group']

            consumer = Consumer(**kafka_conf)
            consumer.subscribe(client_conf['message_type'])
            self._clients[client_type][client_conf['client_id']] = consumer

    def send(self, producer_id: str, message_type: str, method: str, \
        messages: list, timeout=0.1):
        """ Sends list of messages to Kafka cluster(s) """
        producer = self._clients['producer'][producer_id]
        if producer is None:
            raise MessageBusError(errno.EINVAL, "Producer %s is not \
                initialized", producer_id)

        for message in messages:
            producer.produce(message_type, bytes(message, 'utf-8'))
            if method == 'sync':
                producer.flush()
            else:
                producer.poll(timeout=timeout)

    def get_log_size(self, message_type: str):
        """ Gets size of log across all the partitions """
        total_size = 0
        cmd = "/opt/kafka/bin/kafka-log-dirs.sh --describe --bootstrap-server "\
            + self._servers + " --topic-list " + message_type
        try:
            cmd_proc = SimpleProcess(cmd)
            run_result = cmd_proc.run()
            decoded_string = run_result[0].decode('utf-8')
            output_json = json.loads(re.search(r'({.+})', decoded_string).\
                group(0))
            for brokers in output_json['brokers']:
                partition = brokers['logDirs'][0]['partitions']
                for each_partition in partition:
                    total_size += each_partition['size']
            return total_size
        except Exception as e:
            raise MessageBusError(errno.EINVAL, "Unable to fetch log size for \
                message type %s. %s" , message_type, e)

    def delete(self, message_type: str):
        """ Deletes all the messages from Kafka cluster(s) """
        for tuned_retry in range(self._max_config_retry_count):
            self._resource.set_config('retention.ms', \
                self._min_msg_retention_period)
            tuned_params = self._admin.alter_configs([self._resource])
            if list(tuned_params.values())[0].result() is not None:
                if tuned_retry > 1:
                    raise MessageBusError(errno.EINVAL, "Unable to change \
                        retention for %s", message_type)
                continue
            else:
                break

        for retry_count in range(1, (self._max_purge_retry_count + 2)):
            if retry_count > self._max_purge_retry_count:
                raise MessageBusError(errno.EINVAL, "Unable to delete \
                    messages for %s", message_type)
            time.sleep(0.1*retry_count)
            log_size = self.get_log_size(message_type)
            if log_size == 0:
                break

        for default_retry in range(self._max_config_retry_count):
            self._resource.set_config('retention.ms', self._saved_retention)
            default_params = self._admin.alter_configs([self._resource])
            if list(default_params.values())[0].result() is not None:
                if default_retry > 1:
                    raise MessageBusError(errno.EINVAL, "Unknown configuration \
                        for %s", message_type)
                continue
            else:
                break

    def receive(self, consumer_id: str, timeout=0.5) -> list:
        """ Receives list of messages from Kafka cluster(s) """
        consumer = self._clients['consumer'][consumer_id]
        if consumer is None:
            raise MessageBusError(errno.EINVAL, "Consumer %s is not \
                initialized", consumer_id)

        try:
            msg = consumer.poll(timeout=timeout)
            if msg is None:
                pass
            if msg.error():
                raise MessageBusError(errno.ECONN, "Cant receive. %s", \
                    msg.error())
            else:
                return msg.value()
        except KeyboardInterrupt:
            raise MessageBusError(errno.EINVAL, "Cant Recieve %s")

    def ack(self, consumer_id: str):
        """ To manually commit offset """
        consumer = self._clients['consumer'][consumer_id]
        if consumer is None:
            raise MessageBusError(errno.EINVAL, "Consumer %s is not \
                initialized", consumer_id)
        consumer.commit(async=False)
