#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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


import unittest
from cortx.utils.message_bus import MessageProducer, MessageConsumer


class TestMessage(unittest.TestCase):
    """ Test MessageBus related functionality """

    _msg_type = "biggg"
    _consumer_group = "connn"
    _msg_count = 100
    _receive_limit = 10

    def test_delete_count(self):
        """ Test Delete """
        producer = MessageProducer(producer_id="p1", \
            message_type=TestMessage._msg_type, method="sync")
        producer.delete()
        unread_count = producer.get_unread_count \
            (consumer_group=TestMessage._consumer_group)
        self.assertEqual(unread_count, 0)
        self.assertFalse(unread_count > 0)

    def test_send_count(self):
        """ Test Send Message """
        producer = MessageProducer(producer_id="p1", \
            message_type=TestMessage._msg_type, method="sync")
        messages = []
        for i in range(0, TestMessage._msg_count):
            messages.append("This is message" + str(i))
        self.assertEqual(len(messages), TestMessage._msg_count)
        self.assertIsInstance(messages, list)
        producer.send(messages)
        unread_count = producer.get_unread_count(
            consumer_group=TestMessage._consumer_group)
        self.assertEqual(unread_count, TestMessage._msg_count)
        self.assertFalse(unread_count != 100)

    def test_receive_count(self):
        """ Test Unread Message Count """
        read_count = 0
        consumer = MessageConsumer(consumer_id="c1", \
            consumer_group=TestMessage._consumer_group, \
            message_types=[TestMessage._msg_type], auto_ack=True, \
            offset="latest")

        while True:
            message = consumer.receive(timeout=0)
            if message is not None:
                read_count += 1
                consumer.ack()
            if read_count == TestMessage._receive_limit:
                break

        unread_count = consumer.get_unread_count \
            (message_type=TestMessage._msg_type)
        self.assertEqual(unread_count, (TestMessage._msg_count - \
                                        TestMessage._receive_limit))
        self.assertNotEqual(unread_count, TestMessage._msg_count)


if __name__ == "__main__":
    suite = unittest.TestSuite()
    suite.addTest(TestMessage("test_delete_count"))
    suite.addTest(TestMessage("test_send_count"))
    suite.addTest(TestMessage("test_receive_count"))

    runner = unittest.TextTestRunner()
    runner.run(suite)