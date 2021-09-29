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
from cortx.utils.common import CortxConf


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
    def get_server_list(cluster_conf_index: str) -> tuple:
        """Fetches info of nodes in cluster from passed template file.

        Args:
            cluster_conf_index (str): index for loaded input template file

        Raises:
            SetupError: if message bus type not kafka or missing required keys

        Returns:
            tuple: ([server_list], [port_list])
        """
        key_list = ['cortx>utils>message_bus_backend', \
            'cortx>external>kafka>endpoints']

        ConfKeysV().validate('exists', cluster_conf_index, key_list)
        msg_bus_type = Conf.get(cluster_conf_index, key_list[0])

        if msg_bus_type != 'kafka':
            Log.error(f"Message bus type {msg_bus_type} is not supported")
            raise SetupError(errno.EINVAL, \
                "Message bus type %s is not supported", msg_bus_type)

        all_servers = Conf.get(cluster_conf_index, key_list[1])
        message_server_list = []
        port_list = []

        for server in all_servers:
            # Value of server can be <server_fqdn:port> or <server_fqdn>
            if ':' in server:
                server_fqdn, port = server.split(':')
                message_server_list.append(server_fqdn)
                port_list.append(port)
            else:
                message_server_list.append(server)
                port_list.append('9092')   # 90992 is default kafka server port

        if not message_server_list:
            Log.error(f"Missing config entry {key_list} in input file")
            raise SetupError(errno.EINVAL, \
                "Missing config entry %s in config", key_list)

        # Read the default config
        config = CortxConf.get('message_bus')
        return message_server_list, port_list, config


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
