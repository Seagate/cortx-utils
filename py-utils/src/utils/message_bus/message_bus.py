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

from src.utils.message_bus.message_broker_factory import MessageBrokerFactory
from src.utils.message_bus.exceptions import MessageBusError
from src.utils.schema import Conf

class MessageBus():
    """
    An interface that initialize message brokers
    and creates message clients (i.e) producer or consumer
    """
    def __init__(self):
        Conf.load('global', '/etc/cortx/message_bus.json')
        self.message_broker = Conf.get('global', 'message.broker')
        message_broker_factory = MessageBrokerFactory(self.message_broker)
        self.adapter, self.admin = message_broker_factory.adapter, message_broker_factory.admin

    def create(self, client, client_id, consumer_group=None, message_type=None, offset=None):
        create_client = self.adapter.create(client, client_id, consumer_group, message_type, offset)
        return create_client

    def send(self, producer, messages):
            try:
                self.adapter.send(producer, messages)
            except Exception as e:
                print(e)
                raise MessageBusError

    def receive(self):
        consumer_obj = self.adapter.receive()
        return consumer_obj


class MessageBusClient():
    """
    A common Interface that takes either producer/ consumer
    client as input to set the configurations
    """
    def __init__(self, message_bus, client, client_id=None, consumer_group=None, message_type=None, offset=None):
        self._client = client
        self._client_id = client_id
        self._message_bus = message_bus
        self._message_type = message_type
        self._consumer_group = consumer_group
        self._offset = offset
        self._bus_client = self._message_bus.create(self._client, self._client_id,
                                                    self._consumer_group, self._message_type, offset)

    def send(self, messages):
        self._message_bus.send(self._bus_client, messages)

    def receive(self):
        return self._message_bus.receive()
