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

import sys
import inspect
import errno
from collections import namedtuple
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient
from cortx.utils.schema import Conf
from cortx.utils.message_bus.error import MessageBusError

ConsumerRecord = namedtuple("ConsumerRecord",
                            ["message_type", "message", "partition", "offset", "key"])


class MessageBrokerFactory:
    """
    A layer to choose the type of Message Brokers.
    This module helps us to read Broker specific configurations
    and generate Broker specific administrators.
    """

    _brokers = {}

    @staticmethod
    def get_instance(broker_type: str):
        try:
            brokers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
            for name, cls in brokers:
                if name != 'MessageBroker' and name.endswith("Broker"):
                    if broker_type == cls.name:
                        message_broker = cls(Conf)
                        MessageBrokerFactory._brokers[broker_type] = message_broker
                        return message_broker
        except Exception as e:
            raise MessageBusError(errno.EINVAL, "Invalid broker name . %s", e)


class MessageBroker:
    """ A common interface of Message Brokers"""

    def __init__(self, config):
        self._servers = ','.join([str(server) for server in config.get('global', 'message_broker.servers')])

    def send(self, messages: str):
        pass

    def receive(self) -> list:
        pass


class KafkaMessageBroker(MessageBroker):
    """ Kafka Server based message broker implementation """

    name = 'kafka'

    def __init__(self, config):
        """ Initialize Kafka based Administrator based on provided Configurations """
        super().__init__(config)
        self.config = {'bootstrap.servers': self._servers}

        self.message_type = None
        self.producer = None
        self.consumer = None
        self.method = None
        self.admin = AdminClient(self.config)

    def get_client(self, client: str, **client_config):
        """ Initialize Kafka based Producer/Consumer based on provided Configurations """

        producer_config = {}
        consumer_config = {}
        try:
            self.message_type = client_config['message_type']
            if client == 'PRODUCER':
                self.method = client_config['method']
                producer_config['bootstrap.servers'] = self.config['bootstrap.servers']
                if client_config['client_id']:
                    producer_config['client.id'] = client_config['client_id']
                self.producer = Producer(**producer_config)

            elif client == 'CONSUMER':
                consumer_config['bootstrap.servers'] = self.config['bootstrap.servers']
                if client_config['client_id']:
                    consumer_config['client.id'] = client_config['client_id']
                if client_config['offset']:
                    consumer_config['auto.offset.reset'] = client_config['offset']
                if client_config['consumer_group']:
                    consumer_config['group.id'] = client_config['consumer_group']
                self.consumer = Consumer(**consumer_config)
                self.consumer.subscribe(self.message_type)

            else:
                assert client == 'PRODUCER' or client == 'CONSUMER'

        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Invalid Kafka {client} configurations. %s", e)

    def send(self, messages: list):
        """ Sends list of messages to Kafka cluster(s) """
        for each_message in messages:
            self.producer.produce(self.message_type, bytes(each_message, 'utf-8'))
            if self.method == 'sync':
                self.producer.flush()
        self.producer.flush()

    def receive(self) -> list:
        """ Receives list of messages to Kafka cluster(s) """
        msg_list = self._receive_subscribed(self.consumer)
        return msg_list

    def _receive_subscribed(self, consumer: object):
        """ Poll on consumer messages """
        try:
            while True:
                msg = consumer.poll(timeout=0.5)
                if msg is None:
                    continue
                if msg.error():
                    raise MessageBusError(msg.error())
                else:
                    sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                                     (msg.topic(), msg.partition(), msg.offset(),
                                      str(msg.key())))
                    yield ConsumerRecord(msg.topic(), msg.value(), msg.partition(), msg.offset(), str(msg.key()))

        except KeyboardInterrupt:
            sys.stderr.write('%% Aborted by user\n')

    def ack(self):
        """ To manually commit offset """
        self.consumer.commit()
        self.consumer.close()

