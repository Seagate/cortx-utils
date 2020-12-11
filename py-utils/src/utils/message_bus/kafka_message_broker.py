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
from collections import namedtuple
from confluent_kafka import Producer, Consumer
from confluent_kafka.admin import AdminClient
from src.utils.message_bus.message_broker import MessageBroker
from src.utils.message_bus.exceptions import MessageBusError

ConsumerRecord = namedtuple("ConsumerRecord",
                            ["message_type", "message", "partition", "offset", "key"])


class KafkaMessageBroker(MessageBroker):
    """
    Kafka Server based message broker implementation
    """
    def __init__(self, config):
        self.config = config
        self.message_type = None
        self.producer = None
        self.consumer = None

    def create_admin(self):
        try:
            config = {'bootstrap.servers': self.config.get('global', 'bootstrap.servers')}
            admin = AdminClient(config)
            return admin
        except Exception as e:
            raise MessageBusError(f"Invalid Client configuration. {e}")

    def send(self, producer, message):
        for each_message in message:
            producer.produce(self.message_type, bytes(each_message, 'utf-8'))
        producer.flush()

    def receive(self):
        msg_list = self.receive_subscribed(self.consumer)
        return msg_list

    def receive_subscribed(self, consumer):
        try:
            while True:
                msg = consumer.poll(timeout=0.5)
                if msg is None:
                    continue
                if msg.error():
                    raise KafkaException(msg.error())
                else:
                    sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                                     (msg.topic(), msg.partition(), msg.offset(),
                                      str(msg.key())))
                    yield ConsumerRecord(msg.topic(), msg.value(), msg.partition(), msg.offset(), str(msg.key()))

        except KeyboardInterrupt:
            sys.stderr.write('%% Aborted by user\n')

    def create(self, client, consumer_group, message_type, offset):
        try:
            self.message_type = message_type
            config = {}
            if client == 'PRODUCER':
                config['bootstrap.servers'] = self.config.get('global', 'bootstrap.servers')
                self.producer = Producer(**config)
                return self.producer
            elif client == 'CONSUMER':
                config['bootstrap.servers'] = self.config.get('global', 'bootstrap.servers')
                config['enable.auto.commit'] = self.config.get('global', 'enable.auto.commit')
                if offset:
                    config['auto.offset.reset'] = offset
                if consumer_group:
                    config['group.id'] = consumer_group
                self.consumer = Consumer(**config)
                self.consumer.subscribe(self.message_type)
                return self.consumer
            else:
                assert client == 'PRODUCER' or client == 'CONSUMER'
        except Exception as e:
            raise MessageBusError(f"Invalid {client} config. {e}")
