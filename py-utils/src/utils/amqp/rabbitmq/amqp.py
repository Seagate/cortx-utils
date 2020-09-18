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

import time
import logging
import pika
import random
import json
from functools import partial
from pika.exceptions import AMQPConnectionError, AMQPError, ChannelClosedByBroker, \
    ChannelWrongStateError
from cortx.utils.comm import Channel, Comm
from cortx.utils.amqp import const
from cortx.utils.errors import AmqpConnectionError


Log = logging.getLogger(__name__)

class RabbitMQAmqpChannel(Channel):
    """
    Represents Amqp channel to a node for communication
    Communication to node is taken care by this class using pika
    """

    def __init__(self, **kwargs):
        """
        @param kwargs: keyword arguments for RabbitMQ configs
        """
        Channel.__init__(self)
        self._connection = None
        self._channel = None
        self.exchange = kwargs.get(const.EXCH)
        self.exchange_queue = kwargs.get(const.EXCH_QUEUE)
        self.routing_key = kwargs.get(const.ROUTING_KEY)
        self.connection_exceptions = (AMQPConnectionError,
            ChannelClosedByBroker, ChannelWrongStateError, AttributeError)
        self.connection_error_msg = (
            'RabbitMQ channel closed with error {}. Retrying with another host...')
        self.hosts = kwargs.get(const.RMQ_HOSTS)
        self.port = kwargs.get(const.PORT)
        self.virtual_host = kwargs.get(const.VHOST)
        self.username = kwargs.get(const.UNAME)
        self.password = kwargs.get(const.PASS)
        self.exchange_type = kwargs.get(const.EXCH_TYPE)
        self.retry_counter = kwargs.get(const.RETRY_COUNT)
        self.durable = kwargs.get(const.DURABLE)
        self.exclusive = kwargs.get(const.EXCLUSIVE)

    def init(self):
        """
        Initialize the object from a configuration file.
        Establish connection with Rabbit-MQ server.
        """
        self._connection = None
        self._channel = None
        retry_count = 0
        while not(self._connection and self._channel) and \
            int(self.retry_counter) > retry_count:
            self.connect()
            if not (self._connection and self._channel):
                Log.warn(f"RMQ Connection Failed. Retry Attempt: {retry_count+1}"
                    f" in {2**retry_count} seconds")
                time.sleep(2**retry_count)
                retry_count += 1
            else:
                Log.debug(f"RMQ connection is Initialized. Attempts:{retry_count+1}")
        if(self._connection and self._channel):
            self._declare_exchange_and_queue()
        else:
            raise AmqpConnectionError("AMQP connection initialization failed")

    def _declare_exchange_and_queue(self):
        if(self._connection and self._channel):
            try:
                self._channel.exchange_declare(exchange=self.exchange,
                                           exchange_type=self.exchange_type,
                                                   durable=self.durable)
            except AMQPError as err:
                Log.error('Exchange: [{%s}], type: [ {%s} ] cannot be declared.\
                           Details: {%s}'%(self.exchange,
                                              self.exchange_type,
                                              str(err)))
            try:
                self._channel.queue_declare(queue=self.exchange_queue,
                                            exclusive=self.exclusive,
                                                    durable=self.durable)
                self._channel.queue_bind(exchange=self.exchange,
                                         queue=self.exchange_queue,
                                         routing_key=self.routing_key)
                Log.info(f'Initialized Exchange: {self.exchange}, '
                        f'Queue: {self.exchange_queue}, routing_key: {self.routing_key}')
            except AMQPError as err:
                Log.error(f'Fails to initialize the AMQP queue.\
                      Details: {err}')
                Log.exception(err)
                raise AMQPError(-1, f'{err}')

    def connect(self):
        """
        Initiate the connection with RMQ and open the necessary communication channel.
        """
        try:
            ampq_hosts = [f'amqp://{self.username}:{self.password}@{host}/{self.virtual_host}'
                for host in self.hosts]
            ampq_hosts = [pika.URLParameters(host) for host in ampq_hosts]
            random.shuffle(ampq_hosts)
            self._connection = pika.BlockingConnection(ampq_hosts)
            self._channel = self._connection.channel()
        except self.connection_exceptions as e:
            Log.error(self.connection_error_msg.format(repr(e)))

    def disconnect(self):
        """
        Disconnect the connection
        """
        try:
            if self._connection:
                consumer_tag = const.CONSUMER_TAG
                self._channel.basic_cancel(consumer_tag=consumer_tag)
                self._channel.stop_consuming()
                self._channel.close()
                self._connection.close()
                self._channel = None
                self._connection = None
                Log.debug("RabbitMQ connection closed.")
        except Exception as e:
            Log.error(f"Error closing RabbitMQ connection. {e}")

    def recv(self, message=None):
        raise Exception('recv not implemented for AMQP Channel')

    def connection(self):
        return self._connection

    def channel(self):
        return self._channel

    def send(self, message):
        """
        Publish the message to SSPL Rabbit-MQ queue.
        @param message: message to be published to queue.
        @type message: str
        """
        try:
            self._channel.basic_publish(exchange=self.exchange,
                routing_key=self.routing_key, body=json.dumps(message))
            Log.info(f"Message Publish to Xchange: {self.exchange},"\
                f"Key: {self.routing_key}, Msg Details: {message}")
        except self.connection_exceptions as e:
            Log.error(self.connection_error_msg.format(repr(e)))
            self.init()
            self.send(message)

    def recv_file(self, remote_file, local_file):
        raise Exception('recv_file not implemented for AMQP Channel')

    def send_file(self, local_file, remote_file):
        raise Exception('send_file not implemented for AMQP Channel')

    def acknowledge(self, delivery_tag=None):
        try:
            self._channel.basic_ack(delivery_tag=delivery_tag)
        except self.connection_exceptions as e:
            Log.error(self.connection_error_msg.format(repr(e)))
            self.init()
            self.acknowledge(delivery_tag)


class RabbitMQAmqpConsumer(Comm):
    def __init__(self, **kwargs):
        Comm.__init__(self)
        self._inChannel = RabbitMQAmqpChannel(**kwargs)
        self.plugin_callback = None
        self.delivery_tag = None
        self._is_disconnect = False

    def init(self):
        self._inChannel.init()

    def send(self, message, **kwargs):
        raise Exception('send not implemented for RabbitMQAmqpConsumer')

    def send_message_list(self, message: list, **kwargs):
        raise Exception('send_message_list not implemented for RabbitMQAmqpConsumer')

    def _alert_callback(self, ct, ch, method, properties, body):
        """
        1. This is the callback method on which we will receive the
           alerts from RMQ channel.
        2. This method will call AlertPlugin class function and will
           send the alert JSON string as parameter.
        Parameters -
        1. ch - RMQ Channel
        2. method - Contains the server-assigned delivery tag
        3. properties - Contains basic properties like delivery_mode etc.
        4. body - Actual alert JSON string
        """
        self.delivery_tag = method.delivery_tag
        self.plugin_callback(body)

    def acknowledge(self):
        self._inChannel.acknowledge(self.delivery_tag)

    def stop(self):
        self.disconnect()

    def recv(self, callback_fn=None, message=None):
        """
        Start consuming the queue messages.
        """
        try:
            consumer_tag = const.CONSUMER_TAG
            self.plugin_callback = callback_fn
            self._inChannel.channel().basic_consume(self._inChannel.exchange_queue,
                    partial(self._alert_callback, consumer_tag), consumer_tag=consumer_tag)
            self._inChannel.channel().start_consuming()
        except self._inChannel.connection_exceptions as e:
            # Currently there are 2 scenarios in which recv method will fail -
            # 1. When RMQ on the current node fails
            # 2. When we stop csm_agent
            # For the 1st case csm should retry to connect to second node.
            # But for the 2nd case since we are closing the app we should not
            # try to re-connect.
            if not self._is_disconnect:
                Log.error(self._inChannel.connection_error_msg.format(repr(e)))
                self.init()
                self.recv(callback_fn)

    def disconnect(self):
        try:
            Log.debug("Disconnecting AMQPSensor RMQ communication")
            self._is_disconnect = True
            self._inChannel.disconnect()
        except Exception as e:
            Log.exception(e)

    def connect(self):
        raise Exception('connect not implemented for RabbitMQAmqpConsumer')

class RabbitMQAmqpProducer(Comm):
    def __init__(self, **kwargs):
        Comm.__init__(self)
        self._outChannel = RabbitMQAmqpChannel(**kwargs)

    def init(self):
        self._outChannel.init()

    def send(self, message, **kwargs):
        self._outChannel.send(message)

    def send_message_list(self, message: list, **kwargs):
        raise Exception('send_message_list not implemented for RabbitMQAmqpProducer')

    def acknowledge(self):
        raise Exception('acknowledge not implemented for RabbitMQAmqpProducer')

    def stop(self):
        self.disconnect()

    def recv(self, callback_fn=None, message=None):
        raise Exception('recv not implemented for RabbitMQAmqpProducer')

    def disconnect(self):
        try:
            Log.debug("Disconnecting RabbitMQAmqpProducer communication")
            self._outChannel.disconnect()
        except Exception as e:
            Log.exception(e)

    def connect(self):
        raise Exception('connect not implemented for RabbitMQAmqpProducer')
