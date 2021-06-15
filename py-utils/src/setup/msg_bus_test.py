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
from cortx.setup import SetupError
from cortx.utils.process import SimpleProcess


class MessageBusTest:
    """ Represents Message Bus Test methods """

    def __init__(self):
        from cortx.utils.message_bus import MessageBusAdmin
        # Create a test topic
        try:
            admin = MessageBusAdmin(admin_id = 'admins')
            admin.register_message_type(message_types=['mytest'], partitions = 1)
            list_topic = admin.list_message_types()
            if 'mytest' not in list_topic:
                raise SetupError(errno.EINVAL, "Failed to test the config." \
                    "Topic creation failed.")
        except Exception as e:
            raise SetupError(errno.EINVAL, "Failed to test the config, %s", e)

    def __del__(self):
        # Delete the test topic
        from cortx.utils.message_bus import MessageBusAdmin
        # deregister_message_type
        try:
            admin = MessageBusAdmin(admin_id = 'admins')
            admin.deregister_message_type(message_types=['mytest'])
            list_topic = admin.list_message_types()
            if 'mytest' in list_topic:
                raise SetupError(errno.EINVAL, "Failed to test the config." \
                    " Deregister topic failed.")
        except Exception as e:
            raise SetupError(errno.EINVAL, \
                             "Failed to test the config, %s", e)

    def send_msg(self, message):
        """ Sends a  message """
        from cortx.utils.message_bus import MessageProducer
        producer = MessageProducer(producer_id='setup', \
            message_type='mytest', method='sync')
        producer.send(message)
        time.sleep(1)

    def receive_msg(self):
        """ Receives a message """
        from cortx.utils.message_bus import MessageConsumer
        consumer = MessageConsumer(consumer_id='setup', \
            consumer_group='provisioner', message_types=['mytest'], auto_ack=False, \
            offset='earliest')
        while True:
            try:
                time.sleep(1)
                message = consumer.receive()
                if message != None:
                    return message
            except Exception as e:
                raise SetupError(errno.EINVAL, "Failed to receive messages." \
                    " Unable to test the config. %s", e)
