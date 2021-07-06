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

import os
import stat
import errno
from cortx.utils.log import Log
from cortx.utils.message_bus.message_broker import MessageBrokerFactory
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError
from cortx.template import Singleton


class MessageBus(metaclass=Singleton):
    """ Message Bus Framework over various types of Message Brokers """

    conf_file = 'json:///etc/cortx/message_bus.conf'

    def __init__(self):
        """ Initialize a MessageBus and load its configurations """
        Conf.load('config_file', 'json:///etc/cortx/cortx.conf',
            skip_reload=True)
        log_level = Conf.get('config_file', 'utils>log_level', 'INFO')
        Log.init('message_bus', '/var/log/cortx/utils/message_bus',
            level=log_level, backup_count=5, file_size_in_mb=5)
        os.chmod("/var/log/cortx/utils/message_bus", stat.S_IRWXU | \
                 stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
        os.chmod("/var/log/cortx/utils/message_bus/message_bus.log", \
            stat.S_IREAD | stat.S_IWRITE | stat.S_IRGRP | stat.S_IWGRP | \
            stat.S_IROTH | stat.S_IWOTH)

        try:
            Conf.load('message_bus', self.conf_file, skip_reload=True)
            self._broker_conf = Conf.get('message_bus', 'message_broker')
            broker_type = self._broker_conf['type']
            Log.info(f"MessageBus initialized as {broker_type}")
        except ConfError as e:
            Log.error(f"MessageBusError: {e.rc} Error while parsing" \
                f" configuration file {self.conf_file}. {e}.")
            raise MessageBusError(e.rc, "Error while parsing " + \
                "configuration file %s. %s.", self.conf_file, e)
        except Exception as e:
            Log.error(f"MessageBusError: {e.rc} Error while parsing" \
                f" configuration file {self.conf_file}. {e}.")
            raise MessageBusError(errno.ENOENT, "Error while parsing " + \
                "configuration file %s. %s.", self.conf_file, e)

        self._broker = MessageBrokerFactory.get_instance(broker_type, \
            self._broker_conf)

    def init_client(self, client_type: str, **client_conf: dict):
        """ To create producer/consumer client based on the configurations """
        self._broker.init_client(client_type, **client_conf)

    def list_message_types(self, client_id: str) -> list:
        """
        Returns list of available message types from the configured message
        broker
        """
        return self._broker.list_message_types(client_id)

    def register_message_type(self, client_id: str, message_types: list, \
        partitions: int):
        """ Registers list of message types in the configured message broker """
        self._broker.register_message_type(client_id, message_types, \
            partitions)

    def deregister_message_type(self, client_id: str, message_types: list):
        """ Deregisters list of message types in the configured message broker """
        self._broker.deregister_message_type(client_id, message_types)

    def add_concurrency(self, client_id: str, message_type: str, \
        concurrency_count: int):
        """ To achieve concurrency among consumers """
        self._broker.add_concurrency(client_id, message_type, concurrency_count)

    def send(self, client_id: str, message_type: str, method: str, \
        messages: list):
        """ Sends list of messages to the configured message broker """
        self._broker.send(client_id, message_type, method, messages)

    def delete(self, client_id: str, message_type: str):
        """ Deletes all the messages from the configured message broker """
        self._broker.delete(client_id, message_type)

    def get_unread_count(self, message_type: str, consumer_group: str):
        """
        Gets the count of unread messages from the configured message
        broker
        """
        return self._broker.get_unread_count(message_type, consumer_group)

    def receive(self, client_id: str, timeout: float = None) -> list:
        """ Receives messages from the configured message broker """
        return self._broker.receive(client_id, timeout)

    def ack(self, client_id: str):
        """ Provides acknowledgement on offset """
        self._broker.ack(client_id)
