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

from cortx.utils.log import Log
from cortx.utils.message_bus import MessageBus
from cortx.utils.message_bus.error import MessageBusError


class MessageBusClient:
    """ common infrastructure for producer and consumer """

    def __init__(self, client_type: str, cluster_conf: str, **client_conf: dict):
        self._message_bus = MessageBus(cluster_conf) if 'message_bus' not in \
            client_conf.keys() or client_conf['message_bus'] is None else \
            client_conf['message_bus']
        self._message_bus.init_client(client_type, **client_conf)
        self._client_conf = client_conf
        Log.debug(f"MessageBusClient: initialized with arguments" \
            f" client_type: {client_type}, kwargs: {client_conf}")

    def _get_conf(self, key: str):
        """ To get the client configurations """
        if key not in self._client_conf.keys():
            Log.error(f"MessageBusError: {errno.ENOENT}. Could not" \
                f" find key {key} in conf file {self._message_bus.conf_file}")
            raise MessageBusError(errno.ENOENT, "Could not find key %s in " +\
                "conf file %s", key, self._message_bus.conf_file)
        return self._client_conf[key]

    def list_message_types(self) -> list:
        """ Returns list of available message types """
        client_id = self._get_conf('client_id')
        return self._message_bus.list_message_types(client_id)

    def register_message_type(self, message_types: list, partitions: int):
        """
        Registers a list of message types

        Parameters:
        message_types    This is essentially equivalent to the list of queue
                         topic name. For e.g. ["Alert"]
        partitions       Integer that represents number of partitions to be
                         created.
        """
        client_id = self._get_conf('client_id')
        self._message_bus.register_message_type(client_id, message_types, \
            partitions)

    def deregister_message_type(self, message_types: list):
        """
        Deregisters a list of message types

        Parameters:
        message_types    This is essentially equivalent to the list of queue
                         topic name. For e.g. ["Alert"]
        """
        client_id = self._get_conf('client_id')
        self._message_bus.deregister_message_type(client_id, message_types)

    def add_concurrency(self, message_type: str, concurrency_count: int):
        """
        To achieve concurrency for a message type

        Parameters:
        message_type         This is essentially equivalent to queue/topic name.
                             For e.g. "Alert"
        concurrency_count    Integer to achieve concurrency among consumers
        """
        client_id = self._get_conf('client_id')
        self._message_bus.add_concurrency(client_id, message_type, \
            concurrency_count)

    @staticmethod
    def _get_str_message_list(messages: list) -> list:
        """ Convert the format of message to string """
        from cortx.utils.kv_store import KvPayload

        message_list = []
        for message in messages:
            if isinstance(message, KvPayload):
                message = message.json

            if not isinstance(message, str):
                raise MessageBusError(errno.EINVAL, "Invalid message format, \
                    not of type KvPayload or str. %s", message)
            message_list.append(message)
        return message_list

    def send(self, messages: list):
        """
        Sends list of messages to the Message Bus

        Parameters:
        messages     A list of messages sent to Message Bus
        """
        message_type = self._get_conf('message_type')
        method = self._get_conf('method')
        client_id = self._get_conf('client_id')
        messages = self._get_str_message_list(messages)
        self._message_bus.send(client_id, message_type, method, messages)

    def delete(self):
        """ Deletes the messages """
        message_type = self._get_conf('message_type')
        client_id = self._get_conf('client_id')
        return self._message_bus.delete(client_id, message_type)

    def set_message_type_expire(self, message_type: str, expire_time: int):
        """
        Set expiration time for given message type
        """
        message_type_list = self.list_message_types()
        if message_type not in message_type_list:
            raise MessageBusError(errno.ENOENT, "Unknown topic: Could not"+\
                " find the topic %s in topic list %s", message_type, \
                message_type_list)
        client_id = self._get_conf('client_id')
        return self._message_bus.set_message_type_expire(client_id,\
            message_type, expire_time)

    def receive(self, timeout: float = None) -> list:
        """
        Receives messages from the Message Bus

        Parameters:
        timeout     Time in seconds to wait for the message.
        """
        client_id = self._get_conf('client_id')
        return self._message_bus.receive(client_id, timeout)

    def ack(self):
        """ Provides acknowledgement on offset """
        client_id = self._get_conf('client_id')
        self._message_bus.ack(client_id)


class MessageBusAdmin(MessageBusClient):
    """ A client that do admin jobs """

    def __init__(self, admin_id: str, message_bus: MessageBus = None, \
         cluster_conf: str = 'yaml:///etc/cortx/cluster.conf'):
        """ Initialize a Message Admin

        Parameters:
        message_bus    An instance of message bus class.
        admin_id       A String that represents Admin client ID.
        """
        super().__init__(client_type='admin', cluster_conf=cluster_conf, \
            client_id=admin_id, message_bus=message_bus)


class MessageProducer(MessageBusClient):
    """ A client that publishes messages """

    def __init__(self, producer_id: str, message_type: str,
        message_bus: MessageBus = None, method: str = None,
        cluster_conf: str = 'yaml:///etc/cortx/cluster.conf'):
        """ Initialize a Message Producer

        Parameters:
        message_bus     An instance of message bus class.
        producer_id     A String that represents Producer client ID.
        message_type    This is essentially equivalent to the
                        queue/topic name. For e.g. "Alert"
        """
        super().__init__(client_type='producer', cluster_conf=cluster_conf, \
            client_id=producer_id, message_type=message_type, method=method, \
            message_bus=message_bus)

    def get_unread_count(self, consumer_group: str):
        """
        Gets the count of unread messages from the Message Bus

        Parameters:
        consumer_group  A String that represents Consumer Group ID.
        """
        message_type = self._get_conf("message_type")
        return self._message_bus.get_unread_count(message_type, consumer_group)


class MessageConsumer(MessageBusClient):
    """ A client that consumes messages """

    def __init__(self, consumer_id: str, consumer_group: str, auto_ack: str,
        message_types: list, offset: str, message_bus: MessageBus = None,
        cluster_conf: str = 'yaml:///etc/cortx/cluster.conf'):
        """ Initialize a Message Consumer

        Parameters:
        message_bus     An instance of message bus class.
        consumer_id     A String that represents Consumer client ID.
        consumer_group  A String that represents Consumer Group ID.
                        Group of consumers can process messages
        message_types   This is essentially equivalent to the list of queue
                        topic name. For e.g. ["Alert"]
        auto_ack        Can be set to "True" or "False"
        offset          Can be set to "earliest" (default) or "latest".
                        ("earliest" will cause messages to be read from the
                        beginning)
        """
        super().__init__(client_type='consumer', cluster_conf=cluster_conf, \
            client_id=consumer_id, consumer_group=consumer_group, \
            message_types=message_types, auto_ack=auto_ack, offset=offset, \
            message_bus=message_bus)

    def get_unread_count(self, message_type: str):
        """
        Gets the count of unread messages from the Message Bus

        Parameters:
        message_type    This is essentially equivalent to the
                        queue/topic name. For e.g. "Alert"
        """
        consumer_group = self._get_conf("consumer_group")
        return self._message_bus.get_unread_count(message_type, consumer_group)
