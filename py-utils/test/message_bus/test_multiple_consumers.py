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
    """ Test MessageBus related functionality. """

    def test_consumer_one(self):
        """ Test Receive Message for consumer group 1 """
        consumer = MessageConsumer(
            consumer_id='sspl_sensor',
            consumer_group='c1',
            message_types=['test_type'],
            auto_ack=False, offset='latest'
        )

        self.assertIsNotNone(consumer, "Consumer not found")
        count = 0
        while True:
            try:
                message = consumer.receive()
                count += 1
                self.assertIsNotNone(message, "Message not found")
                consumer.ack()
            except Exception as e:
                self.assertEqual(count, 10)
                break

    def test_consumer_two(self):
        """ Test Receive Message for consumer group 2 """
        consumer = MessageConsumer(
            consumer_id='sspl_sensor1',
            consumer_group='c3',
            message_types=['test_type'],
            auto_ack=False, offset='latest'
        )

        self.assertIsNotNone(consumer, "Consumer not found")
        count = 0
        while True:
            try:
                message = consumer.receive()
                count += 1
                self.assertIsNotNone(message, "Message not found")
                consumer.ack()
            except Exception as e:
                self.assertEqual(count, 10)
                break


if __name__ == '__main__':
    unittest.main()
