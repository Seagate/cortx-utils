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
from cortx.utils.message_bus import MessageBus, MessageProducer, MessageConsumer


class TestMessage(unittest.TestCase):
    """ Test MessageBus related functionality """

    message_bus = MessageBus()

    def test_a(self):
        """ Test Send Message """
        messages = []
        producer = MessageProducer(TestMessage.message_bus, \
            producer_id='p1', message_type='big')

        self.assertIsNotNone(producer, "Producer not found")
        for i in range(0, 100):
            messages.append("This is message" + str(i))
        self.assertEqual(len(messages), 100)
        self.assertIsInstance(messages, list)
        producer.send(messages)

    def test_b(self):
        """ Test Unread Message Count """
        consumer = MessageConsumer(TestMessage.message_bus, \
            consumer_id='sensors', consumer_group='test_group', \
            message_types=['big'], auto_ack=True, offset='latest')

        self.assertIsNotNone(consumer, "Consumer not found")
        unread_count = consumer.get_unread_count()
        self.assertEqual(unread_count, 100)


if __name__ == '__main__':
    unittest.main()