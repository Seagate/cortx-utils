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
from cortx.template import Singleton
from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.message_bus.message_broker import MessageBrokerFactory


class MessageBus(metaclass=Singleton):
    """ Message Bus Framework over various types of Message Brokers """
    _broker = None
    _broker_type = 'kafka'
    _receive_timeout = 2
    _socket_timeout = 15000
    _send_timeout = 5000

    @staticmethod
    def init(message_server_endpoints: list, **message_server_params_kwargs: dict):
        """Initialize MessageBus and load its broker."""

        utils_index = 'utils_ind'
        Conf.load(utils_index, 'dict:{}', skip_reload=True)
        message_server_keys = message_server_params_kwargs.keys()

        endpoints = MessageBrokerFactory.get_server_list(message_server_endpoints)
        broker_type = message_server_params_kwargs['broker_type'] if \
            'broker_type' in message_server_keys else MessageBus._broker_type
        receive_timeout = message_server_params_kwargs['receive_timeout'] if \
            'receive_timeout' in message_server_keys else MessageBus._receive_timeout
        socket_timeout = message_server_params_kwargs['socket_timeout'] if \
            'socket_timeout' in message_server_keys else MessageBus._socket_timeout
        send_timeout = message_server_params_kwargs['send_timeout'] if \
            'send_timeout' in message_server_keys else MessageBus._send_timeout

        Conf.set(utils_index, 'message_broker>type', broker_type)
        Conf.set(utils_index, 'message_broker>cluster', endpoints)
        Conf.set(utils_index, 'message_broker>message_bus>receive_timeout', \
            receive_timeout)
        Conf.set(utils_index, 'message_broker>message_bus>socket_timeout', \
            socket_timeout)
        Conf.set(utils_index, 'message_broker>message_bus>send_timeout', \
            send_timeout)
        Conf.save(utils_index)

        try:
            broker_conf = Conf.get(utils_index, 'message_broker')
            Log.info(f"MessageBus initialized as {broker_type}")
        except ConfError as e:
            Log.error(f"MessageBusError: {e.rc} Unable to get broker " \
                f" information. {e}.")
            raise MessageBusError(e.rc, "Unable to get broker " + \
                "information %s. ", e)
        except Exception as e:
            Log.error(f"MessageBusError: {e.rc} Unable to get broker " \
                f" information. {e}.")
            raise MessageBusError(e.rc, "Unable to get broker " + \
                "information %s. ", e)

        MessageBus._broker = MessageBrokerFactory.get_instance(broker_type, \
            broker_conf)

    @staticmethod
    def init_client(client_type: str, **client_conf: dict):
        """To create producer/consumer client based on the configurations."""
        MessageBus._broker.init_client(client_type, **client_conf)

    @staticmethod
    def list_message_types(client_id: str) -> list:
        """
        Returns list of available message types from the configured message
        broker
        """
        return MessageBus._broker.list_message_types(client_id)

    @staticmethod
    def register_message_type(client_id: str, message_types: list, \
        partitions: int):
        """Registers list of message types in the configured message broker."""
        MessageBus._broker.register_message_type(client_id, message_types, \
            partitions)

    @staticmethod
    def deregister_message_type(client_id: str, message_types: list):
        """Deregisters list of message types in the configured message broker."""
        MessageBus._broker.deregister_message_type(client_id, message_types)

    @staticmethod
    def add_concurrency(client_id: str, message_type: str, \
        concurrency_count: int):
        """To achieve concurrency among consumers."""
        MessageBus._broker.add_concurrency(client_id, message_type, concurrency_count)

    @staticmethod
    def send(client_id: str, message_type: str, method: str, messages: list):
        """Sends list of messages to the configured message broker."""
        MessageBus._broker.send(client_id, message_type, method, messages)

    @staticmethod
    def delete(client_id: str, message_type: str):
        """Deletes all the messages from the configured message broker."""
        return MessageBus._broker.delete(client_id, message_type)

    @staticmethod
    def get_unread_count(message_type: str, consumer_group: str):
        """
        Gets the count of unread messages from the configured message
        broker
        """
        return MessageBus._broker.get_unread_count(message_type, consumer_group)

    @staticmethod
    def receive(client_id: str, timeout: float = None) -> list:
        """Receives messages from the configured message broker."""
        return MessageBus._broker.receive(client_id, timeout)

    @staticmethod
    def ack(client_id: str):
        """Provides acknowledgement on offset."""
        MessageBus._broker.ack(client_id)

    @staticmethod
    def set_message_type_expire(client_id: str, message_type: str, \
        expire_time: int):
        """Set expiration time for given message type."""
        return MessageBus._broker.set_message_type_expire(client_id, \
            message_type, expire_time)