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

import errno
import inspect

from cortx.utils import errors
from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from cortx.utils.common.errors import SetupError
from cortx.utils.validator.v_confkeys import ConfKeysV
from cortx.utils.message_bus.error import MessageBusError


class MessageBrokerFactory:
    """ Factory class for Message Brokers """

    _brokers = {}

    @staticmethod
    def get_instance(broker_type: str, broker_conf: dict):
        Log.debug(f"MessageBrokerFactory: invoked with arguments broker_type:" \
            f" {broker_type}, broker_conf: {broker_conf}")
        if broker_type in MessageBrokerFactory._brokers:
            return MessageBrokerFactory._brokers[broker_type]

        from cortx.utils.message_bus import message_broker_collection
        brokers = inspect.getmembers(message_broker_collection, inspect.isclass)
        for name, cls in brokers:
            if name != 'MessageBroker' and name.endswith('Broker'):
                if broker_type == cls.name:
                    message_broker = cls(broker_conf)
                    MessageBrokerFactory._brokers[broker_type] = message_broker
                    return message_broker

        Log.error(f"MessageBusError: {errors.ERR_INVALID_SERVICE_NAME}" \
            f" Invalid service name {broker_type}.")
        raise MessageBusError(errors.ERR_INVALID_SERVICE_NAME, \
            "Invalid service name %s.", broker_type)

    @staticmethod
    def get_server_list(message_server_endpoints: list) -> tuple:
        """Fetches info of nodes in cluster from list of endpoints.

        Args:
            message_server_endpoints: list of endpoints

        Returns:
            list: ([message_server_list])
        """
        message_server_list = []
        server_info = {}
        try:
            for server in message_server_endpoints:
                # Value of server can be <server_fqdn:port> or <server_fqdn>
                if ':' in server:
                    endpoints = server.split('//')[1]
                    server_fqdn, port = endpoints.split(':')
                    server_info['server'] = server_fqdn
                    server_info['port'] = port
                else:
                    server_info['server'] = server
                    server_info['port'] = '9092'  # 9092 is default kafka server port

                message_server_list.append(server_info)
        except Exception as e:
            raise MessageBusError(errno.EINVAL, "Invalid endpoint information." \
                " %s", e)

        return message_server_list


class MessageBroker:
    """ A common interface of Message Brokers"""

    def __init__(self, broker_conf: dict):
        self._servers = ','.join(x['server']+':'+x['port'] for x in \
                                broker_conf['cluster'])

    def init_client(self, **client_conf: dict):
        pass

    def send(self, producer_id: str, message_type: str, method: str, \
        messages: list):
        pass

    def receive(self, consumer_id: str) -> list:
        pass

    def ack(self, consumer_id: str):
        pass
