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

from cortx.utils.message_bus.comm import Channel, Comm
from confluent_kafka import Producer, Consumer, KafkaException
from cortx.utils.message_bus.error import SendError, ConnectionEstError,MsgFetchError, \
    OperationSuccessful, DisconnectError, CommitError
import uuid
from cortx.utils.log import Log
import time
from cortx.utils.message_bus.tcp.kafka import const

class KafkaProducerChannel(Channel):
    """
    Represents kafka producer channel for communication.
    """

    def __init__(self, **kwargs):
        Channel.__init__(self)
        self._hosts = kwargs.get("hosts")
        self._client_id = kwargs.get("client_id")
        self._retry_counter = kwargs.get("retry_counter", 5)
        self._topic = None
        self._channel = None

    def get_topic(self):
        return self._topic

    def set_topic(self, topic):
        if topic:
            self._topic = topic

    def init(self):
        """
        Initialize the object usinf configuration params passed.
        Establish connection with Kafka broker.
        """
        self._channel = None
        retry_count = 0
        try:
            while self._channel is None and int(self._retry_counter) > retry_count:
                self.connect()
                if self._channel is None:
                    Log.warn(f"message bus producer connection Failed. Retry Attempt: {retry_count+1}" \
                        f" in {2**retry_count} seconds")
                    time.sleep(2**retry_count)
                    retry_count += 1
                else:
                    Log.debug(f"message bus producer connection is Initialized."\
                    f"Attempts:{retry_count+1}")
        except Exception as ex:
            Log.error(f"message bus producer initialization failed. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    def connect(self):
        """
        Initiate the connection with Kafka broker and open the
        necessary communication channel.
        """
        try:
            conf = {'bootstrap.servers': str(self._hosts),
                    'request.required.acks' : 'all',
                    'max.in.flight.requests.per.connection': 1,
                    'client.id': self._client_id,
                    'transactional.id': uuid.uuid4(),
                    'enable.idempotence' : True}
            self._channel = Producer(conf)
            self._channel.init_transactions()
        except Exception as ex:
            Log.error(f"Unable to connect to message bus broker. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    @classmethod
    def disconnect(self):
        raise Exception('recv not implemented for Kafka producer Channel')

    @classmethod
    def recv(self, message=None):
        raise Exception('recv not implemented for Kafka producer Channel')

    def channel(self):
        return self._channel

    def send(self, message):
        """
        Publish the message to kafka broker topic.
        """
        try:
            if self._channel is not None:
                self._channel.begin_transaction()
                self._channel.produce(self._topic, message)
                self._channel.commit_transaction()
                Log.info(f"Message Published to Topic: {self._topic},"\
                    f"Msg Details: {message}")
        except KafkaException as e:
            if e.args[0].retriable():
                """Retriable error, try again"""
                self.send(message)
            elif e.args[0].txn_requires_abort():
                """
                Abort current transaction, begin a new transaction,
                and rewind the consumer to start over.
                """
                self._channel.abort_transaction()
                self.send(message)
                #TODO
                #rewind_consumer_offsets...()
            else:
                """Treat all other errors as fatal"""
                Log.error(f"Failed to publish message to topic : {self._topic}. {e}")
                raise SendError(f"Unable to send message to message bus broker. {e}")

    @classmethod
    def recv_file(self, remote_file, local_file):
        raise Exception('recv_file not implemented for Kafka producer Channel')

    @classmethod
    def send_file(self, local_file, remote_file):
        raise Exception('send_file not implemented for Kafka producer Channel')

    @classmethod
    def acknowledge(self, delivery_tag=None):
        raise Exception('send_file not implemented for Kafka producer Channel')

class KafkaConsumerChannel(Channel):
    """
    Represents kafka consumer channel for communication.
    """

    def __init__(self, **kwargs):
        Channel.__init__(self)
        self._hosts = kwargs.get("hosts")
        self._group_id = kwargs.get("group_id")
        self._consumer_name = kwargs.get("consumer_name")
        self._retry_counter = kwargs.get("retry_counter", 5)

    def init(self):
        """
        Initialize the object usinf configuration params passed.
        Establish connection with message bus broker.
        """
        self._channel = None
        retry_count = 0
        try:
            while self._channel is None and int(self._retry_counter) > retry_count:
                self.connect()
                if self._channel is None:
                    Log.warn(f"message bus consumer connection Failed. Retry Attempt: {retry_count+1}" \
                        f" in {2**retry_count} seconds")
                    time.sleep(2**retry_count)
                    retry_count += 1
                else:
                    Log.debug(f"message bus consumer connection is Initialized."\
                    f"Attempts:{retry_count+1}")
        except Exception as ex:
            Log.error(f"message bus consumer initialization failed. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    def connect(self):
        """
        Initiate the connection with Kafka broker and open the
        necessary communication channel.
        """
        try:
            conf = {'bootstrap.servers': str(self._hosts),
                    'group.id' : self._group_id,
                    'group.instance.id' : self._consumer_name,
                    'isolation.level' : 'read_committed',
                    'auto.offset.reset' : 'earliest',
                    'enable.auto.commit' : False}
            self._channel = Consumer(conf)
            Log.info(f"message bus consumer Channel initialized. Group : {self._group_id}")
        except Exception as ex:
            Log.error(f"Unable to connect to message bus broker. {ex}")
            raise ConnectionEstError(f"Unable to connect to message bus broker. {ex}")

    def disconnect(self):
        try:
            self._channel.close()
        except Exception as ex:
            Log.error(f"Closing consumer channel failed. {ex}")
            raise DisconnectError(f"Unable to close the consumer. {ex}")

    @classmethod
    def recv(self, message=None):
        raise Exception('recv not implemented for Kafka consumer Channel')

    def channel(self):
        return self._channel

    @classmethod
    def send(self, message):
        raise Exception('send not implemented for Kafka consumer Channel')

    @classmethod
    def recv_file(self, remote_file, local_file):
        raise Exception('recv_file not implemented for Kafka consumer Channel')

    @classmethod
    def send_file(self, local_file, remote_file):
        raise Exception('send_file not implemented for Kafka consumer Channel')

    def acknowledge(self, delivery_tag=None):
        try:
            self._channel.commit()
        except Exception as ex:
            Log.error(f"Receive commit failed. {ex}")
            raise CommitError(f"Unable to complete commit operation. {ex}")

class KafkaProducerComm(Comm):
    def __init__(self, **kwargs):
        Comm.__init__(self)
        self._outChannel = KafkaProducerChannel(**kwargs)

    def init(self):
        self._outChannel.init()

    def send_message_list(self, message: list, **kwargs):
        if self._outChannel is not None:
            self._outChannel.set_topic(kwargs.get(const.TOPIC))
            for msg in message:
                self.send(msg)
            return OperationSuccessful("Successfully sent messages.")
        else:
            Log.error("Unable to connect to Kafka broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")


    def send(self, message, **kwargs):
        self._outChannel.send(message)

    @classmethod
    def acknowledge(self):
        raise Exception('acknowledge not implemented for KafkaProducer Comm')

    @classmethod
    def stop(self):
        raise Exception('stop not implemented for KafkaProducer Comm')

    @classmethod
    def recv(self, callback_fn=None, message=None, **kwargs):
        raise Exception('recv not implemented for KafkaProducer Comm')

    @classmethod
    def disconnect(self):
        raise Exception('disconnect not implemented for KafkaProducer Comm')

    @classmethod
    def connect(self):
        raise Exception('connect not implemented for KafkaProducer Comm')

class KafkaConsumerComm(Comm):
    def __init__(self, **kwargs):
        Comm.__init__(self)
        self._inChannel = KafkaConsumerChannel(**kwargs)

    def init(self):
        self._inChannel.init()

    @classmethod
    def send_message_list(self, message: list, **kwargs):
        raise Exception('send_message_list not implemented for KafkaConsumer Comm')

    @classmethod
    def send(self, message, **kwargs):
        raise Exception('send not implemented for KafkaConsumer Comm')

    def acknowledge(self):
        if self._inChannel is not None:
            self._inChannel.acknowledge()
            return OperationSuccessful("Commit operation successfull.")
        else:
            Log.error("Unable to connect to message bus broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")

    @classmethod
    def stop(self):
        raise Exception('stop not implemented for KafkaConsumer Comm')

    def recv(self, callback_fn=None, message=None, **kwargs):
        if self._inChannel is not None:
            try:
                self._inChannel.channel().subscribe(kwargs.get(const.TOPIC))
                msg_list = self._inChannel.channel().consume(num_messages=100, timeout=1.0)
            except Exception as ex:
                Log.error(f"Fetching message from kafka broker failed. {ex}")
                raise MsgFetchError(f"No message fetched from kafka broker. {ex}")
        else:
            Log.error("Unable to connect to message bus broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")
        return [msg.value().decode('utf-8') for msg in msg_list]

    def disconnect(self):
        if self._inChannel is not None:
            self._inChannel.disconnect()
            return OperationSuccessful("Close operation successfull.")
        else:
            Log.error("Unable to connect to message bus broker.")
            raise ConnectionEstError("Unable to connect to message bus broker.")

    @classmethod
    def connect(self):
        raise Exception('connect not implemented for KafkaConsumer Comm')
