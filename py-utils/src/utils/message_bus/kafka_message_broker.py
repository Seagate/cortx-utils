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
from confluent_kafka import Producer, Consumer, TopicPartition
from confluent_kafka.admin import AdminClient, NewTopic, ClusterMetadata
from src.utils.message_bus.message_broker import MessageBroker

ConsumerRecord = namedtuple("ConsumerRecord",
                            ["message_type", "message", "partition", "offset", "key"])


class KafkaMessageBroker(MessageBroker):
    """
    A type of broker to send or receive messages across any component
    on a node to any other component on the other
    nodes, reliably and efficiently, using message
    queues protocols
    """
    def __init__(self, config):
        try:
            self.config = config
            self.admin, self.consumer, self.producer = None
        except Exception as e:
            print(e)

    def create_admin(self):
        config = self.config['message_server'][0]
        self.admin = AdminClient(config)
        return self.admin

    def send(self, producer, message, message_type):
        for each_message in message:
            producer.produce(message_type, bytes(each_message.payload, 'utf-8'))
        #producer.flush()

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
                    # Proper message
                    sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                                     (msg.topic(), msg.partition(), msg.offset(),
                                      str(msg.key())))
                    yield ConsumerRecord(msg.topic(), msg.value(), msg.partition(), msg.offset(), str(msg.key()))

        except KeyboardInterrupt:
            sys.stderr.write('%% Aborted by user\n')

    def create(self, client_id, consumer_group, message_type, auto_offset_reset):
        if client_id == 'PRODUCER':
            config = self.config['producer'][0]
            self.producer = Producer(**config)
            return self.producer
        elif client_id == 'CONSUMER':
            config = self.config['consumer'][0]
            if auto_offset_reset:
                config['auto.offset.reset'] = auto_offset_reset
            if consumer_group:
                config['group.id'] = consumer_group
            self.consumer = Consumer(**config)
            self.consumer.subscribe(message_type)
            return self.consumer
        else:
            assert client_id == 'PRODUCER' or client_id == 'CONSUMER'
