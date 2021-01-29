#!/bin/env python3

# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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
import json
import time

from cortx.utils.conf_store import Conf
from cortx.utils.process import SimpleProcess
from cortx.utils.message_bus import MessageBus, MessageConsumer, MessageProducer


class SetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s" %(self._rc, self._desc)



class MessageBusTest:
    """ Represents Message Bus Test methods """

    def __init__(self, server):
        self._server = server
        self._msg_bus = MessageBus()
        # Create a test topic
        cmd = "/opt/kafka/bin/kafka-topics.sh --create" + \
              " --topic my_test --bootstrap-server " + self._server + ":9092"
        try:
            cmd_proc = SimpleProcess(cmd)
            res_op, res_err, res_rc = cmd_proc.run()
            if res_rc != 0:
                raise SetupError(errno.EINVAL, "Unable to test the config")
        except Exception as e:
            raise SetupError(errno.EINVAL, \
                             "Unable to test the config, %s", e)


    def __del__(self):
        # Delete the test topic
        cmd = "/opt/kafka/bin/kafka-topics.sh --delete" + \
              " --topic my_test --bootstrap-server " + self._server + ":9092"
        try:
            cmd_proc = SimpleProcess(cmd)
            res_op, res_err, res_rc = cmd_proc.run()
            if res_rc != 0:
                raise SetupError(errno.EINVAL, "Unable to test the config")
        except Exception as e:
            raise SetupError(errno.EINVAL, \
                             "Unable to test the config, %s", e)


    def send_msg(self, message):
        """ Sends a  message """
        producer = MessageProducer(self._msg_bus, producer_id='setup', \
            message_type='my_test', method='sync')
        producer.send(message)
        time.sleep(1)


    def receive_msg(self):
        """ Receives a message """
        consumer = MessageConsumer(self._msg_bus, consumer_id='setup', \
            consumer_group='provisioner', message_type=['my_test'], auto_ack=False, \
            offset='earliest')
        while True:
            try:
                time.sleep(1)
                message = consumer.receive()
                consumer.ack()
                if message != None:
                    return message
            except Exception as e:
                raise SetupError(errno.EINVAL, \
                             "Unable to test the config, %s", e)


class Utils:
    """ Represents Utils and Performs setup related actions """

    _index = "setup"

    @staticmethod
    def validate(phase: str):
        """ Perform validtions """

        # Perform RPM validations
        pass

    @staticmethod
    def post_install(server):
        """ Performs post install operations """
        cmd = "/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server " \
              + server + ":9092"
        try:
            cmd_proc = SimpleProcess(cmd)
            res_op, res_err, res_rc = cmd_proc.run()
            if res_rc != 0:
                raise SetupError(errno.ENOENT, \
                                 "Seems like Kafka is not running")
        except Exception as e:
            raise SetupError(errno.ENOENT, \
                             "Seems like Kafka is not running, %s", e)
        return res_rc

    @staticmethod
    def init():
        """ Perform initialization """
        return 0

    @staticmethod
    def config(server_list):
        """ Performs configurations """
        with open(r'/etc/cortx/message_bus.conf.new', 'w+') as file:
            json.dump({}, file, indent=2)
        Conf.load("index", "json:///etc/cortx/message_bus.conf.new")
        Conf.set('index', 'message_broker>type', "kafka")
        for i in range(len(server_list)):
            Conf.set('index', f'message_broker>cluster[{i}]', \
                         {"server": server_list[i], "port": "9092"})
        Conf.save('index')
        # copy this conf file as message_bus.conf
        cmd = "/bin/mv /etc/cortx/message_bus.conf.new" + \
              " /etc/cortx/message_bus.conf"
        try:
            cmd_proc = SimpleProcess(cmd)
            res_op, res_err, res_rc = cmd_proc.run()
            if res_rc != 0:
                raise SetupError(errno.EIO, \
                           "/etc/cortx/message_bus.conf file creation failed")
        except Exception as e:
            raise SetupError(errno.EIO, \
                      "/etc/cortx/message_bus.conf file creation failed, %s", e)
        return res_rc

    @staticmethod
    def test(server_list):
        """ Perform configuration testing """
        msg_test = MessageBusTest(server_list[0])
        # Send a message
        msg_test.send_msg(["Test Message"])
        # Recieve the same & validate
        msg = msg_test.receive_msg()
        if str(msg.decode("utf-8")) != "Test Message":
            raise SetupError(errno.EINVAL, "Unable to test the config")
        return 0

    @staticmethod
    def reset():
        """ Performs Configuraiton reset """
        return 0
