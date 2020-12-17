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

import inspect
import errno
from cortx.utils.message_bus.error import MessageBusError


class MessageBrokerFactory:
    """ Factory class for Message Brokers """

    _brokers = {}

    @staticmethod
    def get_instance(broker_type: str, broker_conf: dict):
        if broker_type in MessageBrokerFactory._brokers:
            return MessageBrokerFactory._brokers[broker_type]

        from cortx.utils.message_bus import message_broker_collection
        brokers = inspect.getmembers(message_broker_collection, inspect.isclass)
        for name, cls in brokers:
            if name != 'MessageBroker' and name.endswith("Broker"):
                if broker_type == cls.name:
                    message_broker = cls(broker_conf)
                    MessageBrokerFactory._brokers[broker_type] = message_broker
                    return message_broker

        raise MessageBusError(errno.EINVAL, "Invalid broker type %s. %s", \
            broker_type, e)


class MessageBroker:
    """ A common interface of Message Brokers"""

    def __init__(self, broker_conf):
        # TODO: Handle ports
        self._servers = ','.join(x["server"]+':'+x['port'] for x in \
                                broker_conf['cluster'])

    def init_client(self, **client_conf):
        pass

    def send(self, message_type: str, method: str, messages: str):
        pass

    def receive(self) -> list:
        pass
