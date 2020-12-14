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

from cortx.utils.message_bus.message_broker import MessageBrokerFactory
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.schema import Conf
from cortx.utils.schema.payload import *
import errno


class MessageBus:
    """
    An interface that creates message brokers
    and message clients (i.e) producer or consumer
    """

    def __init__(self):
        """
        Initialize a MessageBus and load its configurations
        """
        Conf.load('global', Json('/etc/cortx/message_bus.json'))
        self.message_broker = Conf.get('global', 'message_broker')
        message_broker_factory = MessageBrokerFactory(self.message_broker['type'])
        self.adapter = message_broker_factory.adapter

    def __call__(self, client, **client_config):
        """
        An instance method of MessageBus to create client based on the configurations
        """
        try:
            self.adapter(client, **client_config)
        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Error creating {client}. {e}")

    def send(self, messages):
        """
        Sends list of messages to the configured message broker
        """
        try:
            self.adapter.send(messages)
        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Error sending message(s). {e}")

    def receive(self):
        """
        Receives messages from the configured message broker
        """
        try:
            consumer_obj = self.adapter.receive()
            return consumer_obj
        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Error receiving message(s). {e}")
