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
from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, ConfigResource, NewTopic, \
    NewPartitions
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
    _max_list_message_type_count = 15

    # Polling timeout
    _default_timeout = 0.5

    # Socket timeout
    _kafka_socket_timeout = 15000

    def __init__(self, broker_conf: dict):
        """ Initialize Kafka based Configurations """
        super().__init__(broker_conf)

        self._clients = {'admin': {}, 'producer': {}, 'consumer': {}}

    def init_client(self, client_type: str, **client_conf: dict):
        """ Obtain Kafka based Producer/Consumer """

        """ Validate and return if client already exists """
        if client_type not in self._clients.keys():
            raise MessageBusError(errno.EINVAL, "Invalid client type %s", \
                client_type)

        if client_conf["client_id"] in self._clients[client_type].keys():
            if self._clients[client_type][client_conf["client_id"]] != {}:
                client = self._clients[client_type][client_conf["client_id"]]
                available_message_types = client.list_topics().topics.keys()
                if client_type == "producer":
                    if client_conf[
                        "message_type"] not in available_message_types:
                        raise KafkaException(KafkaError(3))
                elif client_type == "consumer":
                    if not any(each_message_type in available_message_types for \
                               each_message_type in
                               client_conf["message_types"]):
                        raise KafkaException(KafkaError(3))
                return

        kafka_conf = {}
        kafka_conf['bootstrap.servers'] = self._servers
        kafka_conf['client.id'] = client_conf['client_id']
        kafka_conf['error_cb'] = self._error_cb

        if client_type == 'admin' or self._clients['admin'] == {}:
            if client_type != 'consumer':
                kafka_conf['socket.timeout.ms'] = self._kafka_socket_timeout
                self.admin = AdminClient(kafka_conf)
                self._clients['admin'][client_conf['client_id']] = self.admin

        if client_type == 'producer':
            producer = Producer(**kafka_conf)
            self._clients[client_type][client_conf['client_id']] = producer

            self._resource = ConfigResource('topic', client_conf['message_type'])
            conf = self.admin.describe_configs([self._resource])
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

        elif client_type == 'consumer':
            for entry in ['offset', 'consumer_group', 'message_types', \
                'auto_ack', 'client_id']:
                if entry not in client_conf.keys():
                    raise MessageBusError(errno.EINVAL, "Missing conf entry \
                        %s", entry)

            kafka_conf['enable.auto.commit'] = client_conf['auto_ack']
            kafka_conf['auto.offset.reset'] = client_conf['offset']
            kafka_conf['group.id'] = client_conf['consumer_group']

            consumer = Consumer(**kafka_conf)
            consumer.subscribe(client_conf['message_types'])
            self._clients[client_type][client_conf['client_id']] = consumer

    def _task_status(self, tasks :dict):
        """ Check if the task is completed successfully """
        for message_type, f in tasks.items():
            try:
                f.result()  # The result itself is None
            except Exception as e:
                raise MessageBusError(errno.EINVAL, "Admin operation fails for \
                    %s. %s", message_type, e)

    def _get_metadata(self, admin: object):
        """ To get the metadata information of message type """
        try:
            message_type_metadata = admin.list_topics().__dict__
            return message_type_metadata['topics']
        except Exception as e:
            raise MessageBusError(errno.EINVAL, "Unable to list message type. \
                %s", e)

    @staticmethod
    def _error_cb(err):
        """ Callback to check if all brokers are down """
        if err.code() == KafkaError._ALL_BROKERS_DOWN:
            raise MessageBusError(err.code(), "Kafka Broker(s) are down. %s", \
                err)

    def list_message_types(self, admin_id: str) -> list:
        """
        Returns a list of existing message types.

        Parameters:
        admin_id        A String that represents Admin client ID.

        Return Value:
        Returns list of message types e.g. ["topic1", "topic2", ...]
        """
        admin = self._clients['admin'][admin_id]
        return list(self._get_metadata(admin).keys())

    def register_message_type(self, admin_id: str, message_types: list, \
        partitions: int):
        """
        Creates a list of message types.

        Parameters:
        admin_id        A String that represents Admin client ID.
        message_types   This is essentially equivalent to the list of
                        queue/topic name. For e.g. ["Alert"]
        partitions      Integer that represents number of partitions to be
                        created.
        """
        admin = self._clients['admin'][admin_id]
        new_message_type = [NewTopic(each_message_type, \
            num_partitions=partitions) for each_message_type in message_types]
        created_message_types = admin.create_topics(new_message_type)
        self._task_status(created_message_types)

        for each_message_type in message_types:
            for list_retry in range(1, self._max_list_message_type_count+2):
                if each_message_type not in \
                    list(self._get_metadata(admin).keys()):
                    if list_retry > self._max_list_message_type_count:
                        raise MessageBusError(errno.EINVAL, "Maximum retries \
                            exceeded for creating %s.", each_message_type)
                    time.sleep(list_retry*1)
                    continue
                else:
                    break

    def deregister_message_type(self, admin_id: str, message_types: list):
        """
        Deletes a list of message types.

        Parameters:
        admin_id        A String that represents Admin client ID.
        message_types   This is essentially equivalent to the list of
                        queue/topic name. For e.g. ["Alert"]
        """
        admin = self._clients['admin'][admin_id]
        deleted_message_types = admin.delete_topics(message_types)
        self._task_status(deleted_message_types)

        for each_message_type in message_types:
            for list_retry in range(1, self._max_list_message_type_count+2):
                if each_message_type in list(self._get_metadata(admin).keys()):
                    if list_retry > self._max_list_message_type_count:
                        raise MessageBusError(errno.EINVAL, "Maximum retries \
                            exceeded for deleting %s.", each_message_type)
                    time.sleep(list_retry*1)
                    continue
                else:
                    break

    def add_concurrency(self, admin_id: str, message_type: str, \
        concurrency_count: int):
        """
        Increases the partitions for a message type.

        Parameters:
        admin_id            A String that represents Admin client ID.
        message_type        This is essentially equivalent to queue/topic name.
                            For e.g. "Alert"
        concurrency_count   Integer that represents number of partitions to be
                            increased.

        Note:  Number of partitions for a message type can only be increased,
               never decreased
        """
        admin = self._clients['admin'][admin_id]
        new_partition = [NewPartitions(message_type, \
            new_total_count=concurrency_count)]
        partitions = admin.create_partitions(new_partition)
        self._task_status(partitions)

        # Waiting for few seconds to complete the partition addition process
        for list_retry in range(1, self._max_list_message_type_count+2):
            if concurrency_count != len(self._get_metadata(admin)\
                [message_type].__dict__['partitions']):
                if list_retry > self._max_list_message_type_count:
                    raise MessageBusError(errno.EINVAL, "Maximum retries \
                        exceeded to increase concurrency for %s.", \
                        message_type)
                time.sleep(list_retry*1)
                continue
            else:
                break

    def send(self, producer_id: str, message_type: str, method: str, \
        messages: list, timeout=0.1):
        """
        Sends list of messages to Kafka cluster(s)

        Parameters:
        producer_id     A String that represents Producer client ID.
        message_type    This is essentially equivalent to the
                        queue/topic name. For e.g. "Alert"
        method          Can be set to "sync" or "async"(default).
        messages        A list of messages sent to Kafka Message Server
        """
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

    def delete(self, admin_id: str, message_type: str):
        """
        Deletes all the messages from Kafka cluster(s)

        Parameters:
        message_type    This is essentially equivalent to the
                        queue/topic name. For e.g. "Alert"
        """
        admin = self._clients['admin'][admin_id]

        for tuned_retry in range(self._max_config_retry_count):
            self._resource.set_config('retention.ms', \
                self._min_msg_retention_period)
            tuned_params = admin.alter_configs([self._resource])
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
            default_params = admin.alter_configs([self._resource])
            if list(default_params.values())[0].result() is not None:
                if default_retry > 1:
                    raise MessageBusError(errno.EINVAL, "Unknown configuration \
                        for %s", message_type)
                continue
            else:
                break

    def get_unread_count(self, message_type: str, consumer_group: str):
        """
        Gets the count of unread messages from the Kafka message server

        Parameters:
        message_type    This is essentially equivalent to the
                        queue/topic name. For e.g. "Alert"
        consumer_group  A String that represents Consumer Group ID.
        """
        table = []

        # Update the offsets if purge was called
        if self.get_log_size(message_type) == 0:
            try:
                cmd = "/opt/kafka/bin/kafka-consumer-groups.sh \
                    --bootstrap-server " + self._servers + " --group " \
                    + consumer_group + " --topic " + message_type + \
                    " --reset-offsets --to-latest --execute"
                cmd_proc = SimpleProcess(cmd)
                res_op, res_err, res_rc = cmd_proc.run()
                if res_rc != 0:
                    raise MessageBusError(errno.ENODATA, "Unable to reset the \
                        offsets. %s", res_err)
                decoded_string = res_op.decode("utf-8")
                if "Error" in decoded_string:
                    raise MessageBusError(errno.ENODATA, "Unable to reset the \
                        offsets. %s", decoded_string)
            except Exception as e:
                raise MessageBusError(errno.ENODATA, str(e))

        try:
            cmd = "/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server "\
                + self._servers + " --describe --group " + consumer_group
            cmd_proc = SimpleProcess(cmd)
            res_op, res_err, res_rc = cmd_proc.run()
            if res_rc != 0:
                raise MessageBusError(errno.EINVAL, "Unable to get the message \
                    count. %s", res_err)
            decoded_string = res_op.decode("utf-8")
            if decoded_string == "":
                raise MessageBusError(errno.EINVAL, "No active consumers in \
                    the consumer group, %s", consumer_group)
            elif "Error" in decoded_string:
                raise MessageBusError(errno.EINVAL, "Unable to get the message \
                    count. %s", decoded_string)
            else:
                split_rows = decoded_string.split("\n")
                rows = [row.split(" ") for row in split_rows if row != ""]
                for each_row in rows:
                    new_row = [item for item in each_row if item != ""]
                    table.append(new_row)
                message_type_index = table[0].index("TOPIC")
                lag_index = table[0].index("LAG")
                unread_count = [int(lag[lag_index]) for lag in table if \
                    lag[lag_index] != "LAG" and lag[lag_index] != "-" and \
                    lag[message_type_index] == message_type]

                if len(unread_count) == 0:
                    raise MessageBusError(errno.EINVAL, "No active consumers \
                        in the consumer group, %s", consumer_group)
            return sum(unread_count)

        except Exception as e:
            raise MessageBusError(errno.EINVAL, "Unable to get the message \
                count. %s", e)

    def receive(self, consumer_id: str, timeout: float = None) -> list:
        """
        Receives list of messages from Kafka Message Server

        Parameters:
        consumer_id     Consumer ID for which messages are to be retrieved
        timeout         Time in seconds to wait for the message. Timeout of 0
                        will lead to blocking indefinitely for the message
        """
        consumer = self._clients['consumer'][consumer_id]
        if consumer is None:
            raise MessageBusError(errno.EINVAL, "Consumer %s is not \
                initialized", consumer_id)

        if timeout is None:
            timeout = self._default_timeout

        try:
            while True:
                msg = consumer.poll(timeout=timeout)
                if msg is None:
                    # if blocking (timeout=0), NoneType messages are ignored
                    if timeout > 0:
                        return None
                elif msg.error():
                    raise MessageBusError(errno.ECONN, "Cant receive. %s", \
                        msg.error())
                else:
                    return msg.value()
        except KeyboardInterrupt:
            raise MessageBusError(errno.EINVAL, "Cant Receive %s")

    def ack(self, consumer_id: str):
        """ To manually commit offset """
        consumer = self._clients['consumer'][consumer_id]
        if consumer is None:
            raise MessageBusError(errno.EINVAL, "Consumer %s is not \
                initialized", consumer_id)
        consumer.commit(async=False)