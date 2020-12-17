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

    message_bus = MessageBus()

    def test_send(self):
        """ Test Send Message. """
        messages = []
        producer = MessageProducer(TestMessage.message_bus, producer_id="sspl",\
            message_type="test_type")
        
        self.assertIsNotNone(producer, "Producer not found")
        for i in range(0, 1000):
            messages.append("This is message" + str(i))
        self.assertEqual(len(messages), 1000)
        self.assertIsInstance(messages, list)
        producer.send(messages)

    def test_consumer_one(self):
        """ Test Receive Message for consumer group 1 """
        consumer = MessageConsumer(TestMessage.message_bus, \
            consumer_id="sspl_sensor", consumer_group="c1", \
            message_type=['test_type'], auto_ack=True, offset='latest')

        self.assertIsNotNone(consumer, "Consumer not found")
        messages = consumer.receive()
        self.assertEqual(len(list(messages)), 1000)
        self.assertIsNotNone(messages, "Messages not found")
        for message in messages:
            print(message)
        #consumer.ack()

    def test_consumer_two(self):
        """ Test Receive Message for consumer group 2 """
        consumer = MessageConsumer(TestMessage.message_bus, \
            consumer_id="sspl_sensor1", consumer_group="c3", \
            message_type=['test_type'], auto_ack=True, offset='latest')

        self.assertIsNotNone(consumer, "Consumer not found")
        messages = consumer.receive()
        self.assertEqual(len(list(messages)), 1000)
        self.assertIsNotNone(messages, "Messages not found")
        for message in messages:
            print(message)
        #consumer.ack()


if __name__ == '__main__':
    unittest.main()
