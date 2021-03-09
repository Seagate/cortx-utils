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
import time
from cortx.utils.setup.utils import SetupError
from cortx.utils.process import SimpleProcess


class MessageBusTest:
    """ Represents Message Bus Test methods """

    def __init__(self):
        from cortx.utils.message_bus import MessageBus
        from cortx.utils.conf_store import Conf
        Conf.load("index", "json:///etc/cortx/message_bus.conf")
        self._server = Conf.get("index",'message_broker>cluster[0]>server')
        self._msg_bus = MessageBus()
        # Create a test topic
        cmd = "/opt/kafka/bin/kafka-topics.sh --create" + \
              " --topic mytest --bootstrap-server " + self._server + ":9092"
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
              " --topic mytest --bootstrap-server " + self._server + ":9092"
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
        from cortx.utils.message_bus import MessageProducer
        producer = MessageProducer(self._msg_bus, producer_id='setup', \
            message_type='mytest', method='sync')
        producer.send(message)
        time.sleep(1)

    def receive_msg(self):
        """ Receives a message """
        from cortx.utils.message_bus import MessageConsumer
        consumer = MessageConsumer(self._msg_bus, consumer_id='setup', \
            consumer_group='provisioner', message_types=['mytest'], auto_ack=False, \
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
                             "Unable to test the config. %s", e)
