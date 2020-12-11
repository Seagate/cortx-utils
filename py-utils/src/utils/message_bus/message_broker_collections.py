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
from src.utils.message_bus.exceptions import MessageBusError

ConsumerRecord = namedtuple("ConsumerRecord",
                            ["message_type", "message", "partition", "offset", "key"])


class MessageBroker:
    """ A super abstract class of Message Brokers"""
    def __init__(self):
        pass

    def send(self, producer, topic, message):
        pass

    def receive(self, consumer):
        pass

    def create(self, role):
        pass


class KafkaMessageBroker(MessageBroker):
    """
    Kafka Server based message broker implementation
    """
    name = 'kafka'

    def __init__(self, config):
        servers = ','.join([str(server) for server in config.get('global', 'message_broker')['servers']])
        self.config = {'bootstrap.servers': servers}
        self.message_type = None
        self.producer = None
        self.consumer = None

    def create_admin(self):
        try:
            admin = AdminClient(self.config)
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

    def create(self, client, client_id, consumer_group, message_type, offset):
        try:
            self.message_type = message_type
            if client_id:
                self.config['client.id'] = client_id
            if client == 'PRODUCER':
                self.producer = Producer(**self.config)
                return self.producer
            elif client == 'CONSUMER':
                self.config['enable.auto.commit'] = False
                if offset:
                    self.config['auto.offset.reset'] = offset
                if consumer_group:
                    self.config['group.id'] = consumer_group
                self.consumer = Consumer(**self.config)
                self.consumer.subscribe(self.message_type)
                return self.consumer
            else:
                assert client == 'PRODUCER' or client == 'CONSUMER'
        except Exception as e:
            raise MessageBusError(f"Invalid {client} config. {e}")
