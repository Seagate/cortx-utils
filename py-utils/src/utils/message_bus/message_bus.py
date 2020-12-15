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
    """ Message Bus Framework over various types of Message Brokers """

    def __init__(self):
        """ Initialize a MessageBus and load its configurations """
        try:
            Conf.load('global', Json('/etc/cortx/message_bus.conf'))
            broker_type = Conf.get('global', 'message_broker.type')
            self._message_broker = MessageBrokerFactory.get_instance(broker_type)
        except Exception as e:
            raise MessageBusError(errno.EINVAL, "Invalid Message Bus configurations. %s", e)

    def get_client(self, client: str, **client_config):
        """ To create producer/consumer client based on the configurations """
        try:
            self._message_broker.get_client(client, **client_config)
        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Error creating {client}. %s", e)

    def send(self, messages: list):
        """ Sends list of messages to the configured message broker """
        try:
            self._message_broker.send(messages)
        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Error sending message(s). %s", e)

    def receive(self) -> list:
        """ Receives messages from the configured message broker """
        try:
            consumer_obj = self._message_broker.receive()
            return consumer_obj
        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Error receiving message(s). %s", e)

    def ack(self):
        """ Provides acknowledgement on offset """
        try:
            self._message_broker.ack()
        except Exception as e:
            raise MessageBusError(errno.EINVAL, f"Error committing offsets. %s", e)

