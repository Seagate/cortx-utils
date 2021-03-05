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

from cortx.utils.message_bus import MessageBus


class MessageBusClient:
    """ common infrastructure for producer and consumer """

    def __init__(self, message_bus: MessageBus, client_type: str, \
        **client_conf: dict):
        self._message_bus = message_bus
        self._message_bus.init_client(client_type, **client_conf)
        self._client_conf = client_conf

    def _get_conf(self, key: str):
        """ To get the client configurations """
        if key not in self._client_conf.keys():
            raise MessageBusError(errno.EINVAL, "Invalid entry %s", key) 
        return self._client_conf[key]

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

    def increase_parallelism(self, message_types: list, partitions: int):
        """
        To increase the number of partitions for a list of message types

        Parameters:
        message_types    This is essentially equivalent to the list of queue
                         topic name. For e.g. ["Alert"]
        partitions       Integer that represents number of partitions to be
                         increased.
        """
        client_id = self._get_conf('client_id')
        self._message_bus.increase_parallelism(client_id, message_types, \
            partitions)

    def send(self, messages: list):
        """
        Sends list of messages to the Message Bus

        Parameters:
        messages     A list of messages sent to Message Bus
        """
        message_type = self._get_conf('message_type')
        method = self._get_conf('method')
        client_id = self._get_conf('client_id')
        self._message_bus.send(client_id, message_type, method, messages)

    def delete(self):
        """ Deletes the messages """
        message_type = self._get_conf('message_type')
        client_id = self._get_conf('client_id')
        self._message_bus.delete(client_id, message_type)

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

    def __init__(self, message_bus: MessageBus, admin_id: str):
        """ Initialize a Message Admin

        Parameters:
        message_bus    An instance of message bus class.
        admin_id       A String that represents Admin client ID.
        """
        super().__init__(message_bus, client_type='admin', client_id=admin_id)


class MessageProducer(MessageBusClient):
    """ A client that publishes messages """

    def __init__(self, message_bus: MessageBus, producer_id: str, \
        message_type: str, method: str = None):
        """ Initialize a Message Producer

        Parameters:
        message_bus     An instance of message bus class.
        producer_id     A String that represents Producer client ID.
        message_type    This is essentially equivalent to the
                        queue/topic name. For e.g. "Alert"
        """
        super().__init__(message_bus, client_type='producer', \
            client_id=producer_id, message_type=message_type, method=method)

    def get_unread_count(self, consumer_group: str):
        """
        Gets the count of unread messages from the Message Bus

        Parameters:
        consumer_group  A String that represents Consumer Group ID.
        """
        return self._message_bus.get_unread_count(consumer_group)


class MessageConsumer(MessageBusClient):
    """ A client that consumes messages """

    def __init__(self, message_bus: MessageBus, consumer_id: str, \
        consumer_group: str, message_types: list, auto_ack: str, offset: str):
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
        super().__init__(message_bus, client_type='consumer', \
            client_id=consumer_id, consumer_group=consumer_group, \
            message_types=message_types, auto_ack=auto_ack, offset=offset)

    def get_unread_count(self):
        """ Gets the count of unread messages from the Message Bus """
        consumer_group = self._get_conf('consumer_group')
        return self._message_bus.get_unread_count(consumer_group)