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

from cortx.utils.schema.conf import Conf
from cortx.utils.schema.payload import Json
from cortx.utils.message_bus.tcp.kafka import const
from cortx.utils.message_bus.error import InvalidConfigError, ConnectionEstError
from cortx.utils.message_bus.tcp.kafka.kafka import KafkaProducerComm, KafkaConsumerComm
from cortx.utils.log import Log

class ConfInit:
    __instance = None
    def __init__(self):
        if ConfInit.__instance == None:
            ConfInit.__instance = self
            Conf.init()
            Conf.load(const.CONFIG_INDEX, Json(const.MESSAGE_BUS_CONF))

class MessageBusComm:
    def __init__(self, **kwargs):

        """
        Parameters required for initialization -
        1. comm_type: Type of communication (PRODUCER or CONSUMER)
        2. client_id: Unique string identifying a PRODUCER. For comm_type as
           PRODUCER this field is required.
        3. group_id: This field signifies the consumer group.For comm_type as
           CONSUMER this field is required.
        4. consumer_name: This field signifies the name of the consumer inside
           a consumer group. For comm_type as CONSUMER this field is required.
        """
        #TODO: Add one more field for taking configuration path as a parameter.

        self._comm_obj = None
        self._message_bus_type = None
        self._comm_type = kwargs.get(const.COMM_TYPE, None)
        self._init_config(**kwargs)

    def _init_config(self, **kwargs):
        try:
            #TODO: Write a script to fetch kafka bootstarp cluster and write in
            #the config. Provide the script to Provisioner to copy it to desired
            #location.
            ConfInit()
            self._message_bus_type = Conf.get(const.CONFIG_INDEX, const.TYPE)
            if self._message_bus_type == const.KAFKA:
                self._init_kafka_conf(**kwargs)
            elif self._message_bus_type == const.RMQ:
                self._init_rmq_conf(**kwargs)
            else:
                raise InvalidConfigError("Invalid config")
        except Exception as ex:
            Log.error(f"Invalid config error. {ex}")
            raise InvalidConfigError(f"Invalid config. {ex}")

    def _init_kafka_conf(self, **kwargs):
        kafka_cluster = Conf.get(const.CONFIG_INDEX, \
            f"{const.KAFKA}.{const.CLUSTER}")
        bootstrap_servers = ""
        count = 1
        for values in kafka_cluster:
            if len(kafka_cluster) <= count:
                bootstrap_servers = bootstrap_servers + f"{values[const.SERVER]}:{values[const.PORT]}"
            else:
                bootstrap_servers = bootstrap_servers + f"{values[const.SERVER]}:{values[const.PORT]}, "
            count = count +1
        self._hosts = bootstrap_servers
        self._client_id = kwargs.get(const.CLIENT_ID)
        self._group_id = kwargs.get(const.GROUP_ID)
        self._consumer_name = kwargs.get(const.CONSUMER_NAME)
        self._retry_counter = Conf.get(const.CONFIG_INDEX, \
            f"{const.KAFKA}.{const.RETRY_COUNTER}")
        Log.info(f"Message bus config initialized. Hosts: {self._hosts}, "\
            f"Client ID: {self._client_id}, Group ID: {self._group_id}")

    @classmethod
    def _init_rmq_conf(self, **kwargs):
        raise Exception('init_rmq_conf not implemented in MessageBusComm class')

    def init(self):
        try:
            if self._message_bus_type == const.KAFKA:
                self._comm_obj = self._init_kafka_comm()
            elif self._message_bus_type == const.RMQ:
                self._comm_obj = self._init_rmq_comm()
            self._comm_obj.init()
            Log.debug(f"Initialized the communication channel for {self._comm_type}")
        except Exception as ex:
            Log.error(f"Unable to connect to message bus. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus. {ex}")

    def _init_kafka_comm(self):
        obj = None
        try:
            if self._comm_type == const.PRODUCER:
                obj = KafkaProducerComm(hosts = self._hosts, client_id = self._client_id, \
                    retry_counter = self._retry_counter)
            elif self._comm_type == const.CONSUMER:
                obj = KafkaConsumerComm(hosts = self._hosts, group_id = self._group_id, \
                    retry_counter = self._retry_counter, consumer_name = self._consumer_name)
            return obj
        except Exception as ex:
            Log.error(f"Unable to initialize message bus. {ex}")
            raise ex

    def send(self, message: list, **kwargs):
        try:
            ret = self._comm_obj.send_message_list(message, **kwargs)
            Log.debug("Sent messages to message bus")
            return ret.msg()
        except Exception as ex:
            Log.error(f"Unable to send messages to message bus. {ex}")
            raise ex

    def recv(self, **kwargs):
        try:
            msg = self._comm_obj.recv(**kwargs)
            Log.debug(f"Received message from message bus - {msg}")
            return msg
        except Exception as ex:
            Log.error(f"Unable to receive message from message bus. {ex}")
            raise ex

    def commit(self):
        try:
            ret = self._comm_obj.acknowledge()
            Log.debug("Commited to message bus")
            return ret.msg()
        except Exception as ex:
            Log.error(f"Unable to commit to message bus. {ex}")
            raise ex

    def close(self):
        try:
            ret = self._comm_obj.disconnect()
            Log.debug("Closing the consumer channel")
            return ret.msg()
        except Exception as ex:
            Log.error(f"Unable to close the consumer channel. {ex}")
            raise ex

    @classmethod
    def _init_rmq_comm(self):
        raise Exception('init_rmq_comm not implemented in MessageBusComm class')
