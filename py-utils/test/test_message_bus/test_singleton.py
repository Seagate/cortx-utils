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

    def test_singleton(self):
        """ Test Singleton functionality """

        message_bus_1 = MessageBus()
        message_bus_2 = MessageBus()

        # Check for same instance
        self.assertEqual(message_bus_1, message_bus_2)

        # Send and receive messages without MessageBus instance
        messages = []
        producer = MessageProducer(producer_id='p1', message_type='biggg')
        self.assertIsNotNone(producer, "Producer not found")
        for i in range(0, 10):
            messages.append("This is message" + str(i))
        producer.send(messages)

        consumer = MessageConsumer(consumer_id='msys', consumer_group='connn',
                                   message_types=['biggg'], auto_ack=True, \
                                   offset='latest')
        count = 0
        while True:
            try:
                message = consumer.receive()
                if type(message) is bytes:
                    count += 1
                consumer.ack()
            except Exception as e:
                self.assertEqual(count, 10)
                break


if __name__ == '__main__':
    unittest.main()