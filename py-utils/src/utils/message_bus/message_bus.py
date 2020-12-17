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

    conf_file = "/etc/cortx/message_bus.conf"

    def __init__(self):
        """ Initialize a MessageBus and load its configurations """
        try:
            Conf.load('message_bus', Json(self.conf_file))
            self._broker_conf = Conf.get("message_bus", "message_broker")
            broker_type = self._broker_conf['type']

        except Exception as e:
            raise MessageBusError(errno.EINVAL, "Invalid conf in %s. %s", \
                self.conf_file, e)

        self._broker = MessageBrokerFactory.get_instance(broker_type, \
                self._broker_conf)

    def init_client(self, client_type: str, **client_conf: dict):
        """ To create producer/consumer client based on the configurations """
        self._broker.init_client(client_type, **client_conf)

    def send(self, message_type: str, method: str, messages: list, client_id: str):
        """ Sends list of messages to the configured message broker """
        self._broker.send(message_type, method, messages, client_id)

    def receive(self, client_id: str) -> list:
        """ Receives messages from the configured message broker """
        return self._broker.receive(client_id)

    def ack(self):
        """ Provides acknowledgement on offset """
        self._broker.ack()

