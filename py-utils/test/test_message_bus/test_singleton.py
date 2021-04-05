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
from cortx.utils.message_bus import MessageBus, MessageBusAdmin, MessageProducer, MessageConsumer


class TestMessage(unittest.TestCase):
    """ Test MessageBus related functionality """

    _msg_type = 'biggg'
    _msg_count = 10

    def test_same_instance(self):
        """ Test Singleton functionality """

        message_bus_1 = MessageBus()
        message_bus_2 = MessageBus()
        # Check for same instance
        self.assertEqual(message_bus_1, message_bus_2)

    def test_no_instance(self):
        """ Test Clients with no instance """

        admin = MessageBusAdmin(admin_id='admin')
        self.assertTrue(TestMessage._msg_type in admin.list_message_types())

        messages = []
        producer = MessageProducer(producer_id='p1', \
            message_type=TestMessage._msg_type, method='sync')
        self.assertIsNotNone(producer, "Producer not found")
        for i in range(0, TestMessage._msg_count):
            messages.append("This is message" + str(i))
        producer.send(messages)

        consumer = MessageConsumer(consumer_id='msys', consumer_group='connn', \
            message_types=[TestMessage._msg_type], auto_ack=True, \
            offset='latest')
        count = 0
        while True:
            try:
                message = consumer.receive()
                if isinstance(message, bytes):
                    count += 1
                consumer.ack()
            except Exception:
                self.assertEqual(count, TestMessage._msg_count)
                break

    def test_one_instance(self):
        """ Test Clients with one instance """

        message_bus = MessageBus()
        admin = MessageBusAdmin(admin_id='admin', message_bus=message_bus)
        self.assertTrue(TestMessage._msg_type in admin.list_message_types())

        messages = []
        producer = MessageProducer(producer_id='p1', \
            message_type=TestMessage._msg_type, method='sync', \
            message_bus=message_bus)
        self.assertIsNotNone(producer, "Producer not found")
        for i in range(0, TestMessage._msg_count):
            messages.append("This is message" + str(i))
        producer.send(messages)

        consumer = MessageConsumer(consumer_id='msys', consumer_group='connn', \
            message_types=[TestMessage._msg_type], auto_ack=True, \
            offset='latest', message_bus=message_bus)
        count = 0
        while True:
            try:
                message = consumer.receive()
                if isinstance(message, bytes):
                    count += 1
                consumer.ack()
            except Exception:
                self.assertEqual(count, TestMessage._msg_count)
                break

    def test_multiple_instance(self):
        """ Test Clients with no instance """

        message_bus_1 = MessageBus()
        message_bus_2 = MessageBus()
        message_bus_3 = MessageBus()
        admin = MessageBusAdmin(admin_id='admin', message_bus=message_bus_1)
        self.assertTrue(TestMessage._msg_type in admin.list_message_types())

        messages = []
        producer = MessageProducer(producer_id='p1', \
            message_type=TestMessage._msg_type, method='sync', \
            message_bus=message_bus_2)
        self.assertIsNotNone(producer, "Producer not found")
        for i in range(0, TestMessage._msg_count):
            messages.append("This is message" + str(i))
        producer.send(messages)

        consumer = MessageConsumer(consumer_id='msys', consumer_group='connn', \
            message_types=[TestMessage._msg_type], auto_ack=True, \
            offset='latest', message_bus=message_bus_3)
        count = 0
        while True:
            try:
                message = consumer.receive()
                if isinstance(message, bytes):
                    count += 1
                consumer.ack()
            except Exception:
                self.assertEqual(count, TestMessage._msg_count)
                break


if __name__ == '__main__':
    unittest.main()