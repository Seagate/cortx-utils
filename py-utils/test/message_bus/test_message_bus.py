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
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.message_bus import MessageBus, MessageBusAdmin, \
    MessageProducer, MessageConsumer

# Total messages to be received by consumer threads
total = 0


class TestMessageBus(unittest.TestCase):

    """Test MessageBus related functionality."""

    _message_type = 'test'
    _bulk_count = 25
    _receive_limit = 5
    _admin = MessageBusAdmin(admin_id='register')
    _producer = None
    _consumer = None

    @classmethod
    def setUpClass(cls):
        cls._admin.register_message_type(message_types= \
            [TestMessageBus._message_type], partitions=1)
        cls._producer = MessageProducer(producer_id='send', \
            message_type=TestMessageBus._message_type, method='sync')
        cls._consumer = MessageConsumer(consumer_id='receive', \
            consumer_group='test', message_types=[TestMessageBus._message_type], \
            auto_ack=False, offset='earliest')

    def test_list_message_type(self):
        """Test list message type."""
        message_type_list = TestMessageBus._admin.list_message_types()
        self.assertTrue(TestMessageBus._message_type in message_type_list)
        self.assertFalse(TestMessageBus._message_type not in message_type_list)

    def test_unknown_message_type(self):
        """Test invalid message type."""
        with self.assertRaises(MessageBusError):
            MessageProducer(producer_id='send', \
                message_type='', method='sync')
        with self.assertRaises(MessageBusError):
            MessageConsumer(consumer_id='receive', consumer_group='test', \
                message_types=[''], auto_ack=False, offset='earliest')

    def test_send(self):
        """Test send message."""
        TestMessageBus._producer.send(["A simple test message"])

    def test_receive(self):
        """Test receive message."""
        message = TestMessageBus._consumer.receive(timeout=0)
        self.assertIsNotNone(message, "Message not found")
        TestMessageBus._consumer.ack()

    def test_send_bulk(self):
        """Test send bulk messages."""
        messages = []
        for msg_num in range(0, TestMessageBus._bulk_count):
            messages.append("Test Message " + str(msg_num))
        TestMessageBus._producer.send(messages)

    def test_producer_unread_count(self):
        """Test unread message count from producer."""
        unread_count = TestMessageBus._producer.get_unread_count(\
            consumer_group='test')
        self.assertEqual(unread_count, TestMessageBus._bulk_count)

    def test_consumer_unread_count(self):
        """Test unread message count from consumer."""
        read_count = 0
        while True:
            message = TestMessageBus._consumer.receive(timeout=0)
            if message is not None:
                read_count += 1
                TestMessageBus._consumer.ack()
            if read_count == TestMessageBus._receive_limit:
                break

        unread_count = TestMessageBus._consumer.get_unread_count\
            (message_type=TestMessageBus._message_type)
        self.assertEqual(unread_count, (TestMessageBus._bulk_count - \
            TestMessageBus._receive_limit))

    def test_receive_bulk(self):
        """Test receive bulk messages."""
        count = 0
        while True:
            message = TestMessageBus._consumer.receive()
            if message is None:
                break
            self.assertIsNotNone(message, "Message not found")
            count += 1
        self.assertEqual(count, (TestMessageBus._bulk_count - \
            TestMessageBus._receive_limit))

    def test_receive_different_consumer_group(self):
        """Test receive from different consumer_group."""
        consumer_group = ['group_1', 'group2']
        for cg in consumer_group:
            consumer = MessageConsumer(consumer_id=cg, consumer_group=cg, \
                message_types=[TestMessageBus._message_type], auto_ack=False, \
                offset='earliest')
            count = 0
            while True:
                message = consumer.receive()
                if message is None:
                    break
                self.assertIsNotNone(message, "Message not found")
                count += 1
            self.assertEqual(count, (TestMessageBus._bulk_count + 1))

    def test_register_message_type_exist(self):
        """Test register existing message type."""
        with self.assertRaises(MessageBusError):
            TestMessageBus._admin.register_message_type(message_types=\
                [TestMessageBus._message_type], partitions=1)

    def test_deregister_message_type_not_exist(self):
        """Test deregister not existing message type."""
        with self.assertRaises(MessageBusError):
            TestMessageBus._admin.deregister_message_type(message_types=\
                [''])

    def test_concurrency(self):
        """Test add concurrency count."""
        TestMessageBus._admin.add_concurrency(message_type=\
            TestMessageBus._message_type, concurrency_count=5)

    def test_receive_concurrently(self):
        """Test receive concurrently."""
        messages = []
        for msg_num in range(0, TestMessageBus._bulk_count):
            messages.append("Test Message " + str(msg_num))
        TestMessageBus._producer.send(messages)

        from threading import Thread

        def consumer_1():
            global total
            count = 0
            while True:
                message = TestMessageBus._consumer.receive()
                if message is None:
                    break
                self.assertIsNotNone(message, "Message not found")
                count += 1
            total += count

        def consumer_2():
            global total
            count = 0
            while True:
                message = TestMessageBus._consumer.receive()
                if message is None:
                    break
                self.assertIsNotNone(message, "Message not found")
                count += 1
            total += count

        t1 = Thread(target=consumer_1)
        t2 = Thread(target=consumer_2)
        t1.start()
        t2.start()

        # sleep for thread to complete
        import time
        time.sleep(5)
        self.assertEqual(total, TestMessageBus._bulk_count)

    def test_reduce_concurrency(self):
        """Test reduce concurrency count."""
        with self.assertRaises(MessageBusError):
            TestMessageBus._admin.add_concurrency(message_type=\
                TestMessageBus._message_type, concurrency_count=2)

    def test_singleton(self):
        """Test instance of message_bus."""
        message_bus_1 = MessageBus()
        message_bus_2 = MessageBus()
        self.assertTrue(message_bus_1 is message_bus_2)

    @classmethod
    def tearDownClass(cls):
        """Delete the test message_type."""
        cls._admin.deregister_message_type(message_types=\
            [TestMessageBus._message_type])
        message_type_list = TestMessageBus._admin.list_message_types()
        cls.assertTrue(cls, TestMessageBus._message_type not in \
            message_type_list)
        cls.assertFalse(cls, TestMessageBus._message_type in message_type_list)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(TestMessageBus('test_list_message_type'))
    suite.addTest(TestMessageBus('test_unknown_message_type'))
    suite.addTest(TestMessageBus('test_send'))
    suite.addTest(TestMessageBus('test_receive'))
    suite.addTest(TestMessageBus('test_send_bulk'))
    suite.addTest(TestMessageBus('test_producer_unread_count'))
    suite.addTest(TestMessageBus('test_consumer_unread_count'))
    suite.addTest(TestMessageBus('test_receive_bulk'))
    suite.addTest(TestMessageBus('test_receive_different_consumer_group'))
    suite.addTest(TestMessageBus('test_register_message_type_exist'))
    suite.addTest(TestMessageBus('test_deregister_message_type_not_exist'))
    suite.addTest(TestMessageBus('test_concurrency'))
    suite.addTest(TestMessageBus('test_receive_concurrently'))
    suite.addTest(TestMessageBus('test_reduce_concurrency'))
    suite.addTest(TestMessageBus('test_singleton'))

    runner = unittest.TextTestRunner()
    runner.run(suite)