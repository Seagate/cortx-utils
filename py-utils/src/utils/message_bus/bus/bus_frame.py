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

from src.utils.message_bus.bus.topic import Topic
from src.utils.message_bus.bus.topic_schema import TopicSchema
from src.utils.message_bus.bus.callback import MyCallback
from src.template import Factory, Singleton
from src.utils.message_bus.message_queue_factory import KafkaFactory
from src.utils.message_bus.exceptions import KeyNotFoundError

class MessageBus(metaclass=Singleton):

    def __init__(self, config, bus_callback=MyCallback()):
        self.config = config.get_config()
        self.notifier = None
        self.mapper = {}
        self.callables = {}
        self.bus_callback = bus_callback
        self.m_factory = Factory({
            "kafka": KafkaFactory,
            #"confluent-kafka": ConfluentFactory
        })
        self.__load_adapter(self.config)
        if self.config is not None:
            self.__load_topic()

        self.schema = TopicSchema()
        self.client_list = []

    def __load_adapter(self, config):
        factory = self.m_factory(config)
        self.config, self.adapter, self.admin = factory.config, factory.adapter, factory.admin


    def __load_topic(self):
        # will get the schema from config file . convert the string in config.schema
        # to TopicInMessage using factory patter
        self.schema = TopicSchema()
        for t in self.config['message_type']:
            topic = Topic(t)
            self.schema.set_topic(topic.name, topic)

    def create(self, role, consumer_group=None, message_type=None, auto_offset_reset=None):
        self.role = role
        self.message_type = message_type
        self.consumer_group = consumer_group
        self.bus_callback.precreate_busclient(self.role)
        create_busclient = self.adapter.create(self.role, self.consumer_group, self.message_type, auto_offset_reset)
        self.bus_callback.postcreate_busclient(self.role)

        return create_busclient

    def send(self, producer, message, topic):
        # topic = self.schema.get_topic(producer, message)
        self.bus_callback.pre_send(producer, topic, message)

        all_topic_list = self.get_all_topics()
        if topic in all_topic_list:
            try:
                self.adapter.send(producer, message, topic)
            except:
                raise KeyNotFoundError

        # Will post send consider exception too
        self.bus_callback.post_send(producer, topic, message)


    def get_topic(self, client, message):
        return self.schema.get_topic(client, message)

    def receive(self ):
        #self.bus_callback.pre_receive()
        consumer_obj = self.adapter.receive()

        if self.notifier is not None:
            consumer_obj = self.notifier.get_caller(consumer_obj)

        #self.bus_callback.post_receive()
        return consumer_obj


    def create_topic(self,topic_name, timeout_ms=None, validate_only=False):
        self.bus_callback.precreate_topic(topic_name, timeout_ms=None, validate_only=False)
        self.adapter.create_topics(topic_name, timeout_ms, validate_only)
        self.bus_callback.postcreate_topic(topic_name, timeout_ms=None, validate_only=False)


    def get_all_topics(self):
        # Will return all created topics
        return self.adapter.get_all_topics()

