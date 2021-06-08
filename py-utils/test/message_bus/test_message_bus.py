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
    """Test MessageBus related functionality."""

    def test_send(self):
        """Test Send Message."""
        messages = []
        producer = MessageProducer(
            producer_id='sspl_sensor',
            message_type='Alert'
        )

        self.assertIsNotNone(producer, "Producer not found")
        for i in range(0, 1000):
            messages.append("This is message" + str(i))
        self.assertEqual(len(messages), 1000)
        self.assertIsInstance(messages, list)
        producer.send(messages)

    def test_receive(self):
        """Test Receive Message."""
        consumer = MessageConsumer(
            consumer_id='sspl_sensors',
            consumer_group='sspl',
            message_types=['Alert'],
            auto_ack=False,
            offset='latest'
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
                self.assertEqual(count, 1000)
                break


if __name__ == '__main__':
    unittest.main()
