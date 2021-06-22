#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
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

import json
import unittest
from cortx.utils.conf_store import Conf
from cortx.utils.message_bus import MessageProducer, MessageConsumer


class TestMessage(unittest.TestCase):
    """ Test MessageBus related functionality """

    _file = 'json:///etc/cortx/message_bus.conf'
    _conf_key = 'message_broker'
    _message_type = 'kv_payloads'

    def test_kv_send(self):
        """ Test send kv_payload as message """
        messages = []
        producer = MessageProducer(producer_id='kv_producer', \
            message_type=TestMessage._message_type, method='sync')
        self.assertIsNotNone(producer, "Producer not found")

        # To get the value for particular key
        Conf.load('index', TestMessage._file, skip_reload=True)
        payload = Conf.get('index', TestMessage._conf_key)

        messages.append(json.dumps(payload))
        self.assertIsInstance(messages, list)
        producer.send(messages)

    def test_receive(self):
        """ Test receive kv_payload as message """
        consumer = MessageConsumer(consumer_id='kv_consumer', \
            consumer_group='kv', message_types=[TestMessage._message_type], \
            auto_ack=True, offset='earliest')
        self.assertIsNotNone(consumer, "Consumer not found")

        while True:
            message = consumer.receive()
            if message is None:
                break
            payload = json.loads(message)
            self.assertIs(type(payload), dict)


if __name__ == '__main__':
    unittest.main()