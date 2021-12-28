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

import time
import unittest
from cortx.utils.message_bus.error import MessageBusError
from cortx.utils.message_bus import MessageBus, MessageBusAdmin, \
    MessageProducer, MessageConsumer

# Total messages to be received by consumer threads
total = 0


class TestMessageBus(unittest.TestCase):

    """Test MessageBus related functionality."""

    _message_type = 'test_mb'
    _bulk_count = 25
    _receive_limit = 5
    _purge_retry = 20
    _producer = None
    _consumer = None
    _cluster_conf_path = ''

    @classmethod
    def setUpClass(cls, cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        """Register the test message_type."""
        if TestMessageBus._cluster_conf_path:
            cls.cluster_conf_path = TestMessageBus._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path
        cls._admin = MessageBusAdmin(admin_id='register', \
            cluster_conf = cls.cluster_conf_path)
        cls._admin.register_message_type(message_types= \
            [TestMessageBus._message_type], partitions=1)
        cls._producer = MessageProducer(producer_id='send', \
            message_type=TestMessageBus._message_type, method='sync', \
            cluster_conf = cls.cluster_conf_path)
        cls._consumer = MessageConsumer(consumer_id='receive', \
            consumer_group='test', message_types=[TestMessageBus._message_type], \
            auto_ack=False, offset='earliest', cluster_conf = cls.cluster_conf_path)

    def test_001_list_message_type(self):
        """Test list message type."""
        message_type_list = TestMessageBus._admin.list_message_types()
        self.assertTrue(TestMessageBus._message_type in message_type_list)
        self.assertFalse(TestMessageBus._message_type not in message_type_list)

    def test_002_unknown_message_type(self):
        """Test invalid message type."""
        with self.assertRaises(MessageBusError):
            MessageProducer(producer_id='send', \
                message_type='', method='sync', \
                cluster_conf = TestMessageBus.cluster_conf_path)
        with self.assertRaises(MessageBusError):
            MessageConsumer(consumer_id='receive', consumer_group='test', \
                message_types=[''], auto_ack=False, offset='earliest', \
                cluster_conf = TestMessageBus.cluster_conf_path)

    @staticmethod
    def test_003_send():
        """Test send message."""
        TestMessageBus._producer.send(["A simple test message"])

    def test_004_receive(self):
        """Test receive message."""
        message = TestMessageBus._consumer.receive(timeout=0)
        self.assertIsNotNone(message, "Message not found")
        TestMessageBus._consumer.ack()

    @staticmethod
    def test_005_send_bulk():
        """Test send bulk messages."""
        messages = []
        for msg_num in range(0, TestMessageBus._bulk_count):
            messages.append("Test Message " + str(msg_num))
        TestMessageBus._producer.send(messages)

    def test_006_receive_bulk(self):
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

    def test_007_receive_different_consumer_group(self):
        """Test receive from different consumer_group."""
        consumer_group = ['group_1', 'group2']
        for cg in consumer_group:
            consumer = MessageConsumer(consumer_id=cg, consumer_group=cg, \
                message_types=[TestMessageBus._message_type], auto_ack=False, \
                offset='earliest', cluster_conf = TestMessageBus.cluster_conf_path)
            count = 0
            while True:
                message = consumer.receive()
                if message is None:
                    break
                self.assertIsNotNone(message, "Message not found")
                count += 1
            self.assertEqual(count, (TestMessageBus._bulk_count + 1))

    def test_008_register_message_type_exist(self):
        """Test register existing message type."""
        with self.assertRaises(MessageBusError):
            TestMessageBus._admin.register_message_type(message_types=\
                [TestMessageBus._message_type], partitions=1)

    def test_009_deregister_message_type_not_exist(self):
        """Test deregister not existing message type."""
        with self.assertRaises(MessageBusError):
            TestMessageBus._admin.deregister_message_type(message_types=\
                [''])

    def test_010_purge_messages(self):
        """Test purge messages."""
        rc = TestMessageBus._producer.delete()
        self.assertEqual(rc, 0)
        message = TestMessageBus._consumer.receive()
        self.assertIsNone(message)

    @staticmethod
    def test_011_concurrency():
        """Test add concurrency count."""
        TestMessageBus._admin.add_concurrency(message_type=\
            TestMessageBus._message_type, concurrency_count=5)

    def test_012_receive_concurrently(self):
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

    def test_013_reduce_concurrency(self):
        """Test reduce concurrency count."""
        with self.assertRaises(MessageBusError):
            TestMessageBus._admin.add_concurrency(message_type=\
                TestMessageBus._message_type, concurrency_count=2)

    def test_014_singleton(self):
        """Test instance of message_bus."""
        message_bus_1 = MessageBus()
        message_bus_2 = MessageBus()
        self.assertTrue(message_bus_1 is message_bus_2)

    @staticmethod
    def test_015_multiple_admins():
        """Test multiple instances of admin interface."""
        message_types_list = TestMessageBus._admin.list_message_types()
        message_types_list.remove(TestMessageBus._message_type)
        message_types_list.remove('__consumer_offsets')
        if message_types_list:
            for message_type in message_types_list:
                producer = MessageProducer(producer_id=message_type, \
                    message_type=message_type, method='sync', \
                    cluster_conf = TestMessageBus.cluster_conf_path)
                producer.delete()

    def test_016_set_message_type_expiry(self):
        """Test set message type expiry and read before expiry."""
        # Set expire time to 2 seconds
        TestMessageBus._admin.set_message_type_expire(\
            TestMessageBus._message_type, expire_time_ms=2000,\
                data_limit_bytes=10000)
        TestMessageBus._producer.send(["A simple test message"])
        # get before expire
        message = TestMessageBus._consumer.receive()
        self.assertEqual(message, b'A simple test message')

    def test_017_message_type_read_after_expiry(self):
        """Test receive expired messages."""
        # Do Purge
        for retry_count in range(1, (TestMessageBus._purge_retry + 2)):
            rc = TestMessageBus._producer.delete()
            if retry_count > TestMessageBus._purge_retry:
                self.assertIsInstance(rc, MessageBusError)
            if rc == 0:
                break
            time.sleep(2*retry_count)
        # Set expire time to 3 seconds
        TestMessageBus._admin.set_message_type_expire(\
            TestMessageBus._message_type, expire_time_ms=5000,\
                data_limit_bytes=10000)
        for count in range(3):
            TestMessageBus._producer.send(\
            [f"A simple test message {count}"])
        # Wait for message to expire
        time.sleep(10)
        _consumer_new = MessageConsumer(consumer_id='receive_new', \
            consumer_group='test_new', \
            message_types=[TestMessageBus._message_type], \
            auto_ack=False, offset='earliest', \
            cluster_conf = self.cluster_conf_path)
        message = _consumer_new.receive()
        # Revert back to original timeout to 604800000 (7 days)
        #  and data log size to 1073741824 (1 Gb)
        TestMessageBus._admin.set_message_type_expire(\
            TestMessageBus._message_type, expire_time_ms=604800000,\
                data_limit_bytes=1073741824 )
        self.assertIsNone(message)

    @classmethod
    def tearDownClass(cls):
        """Deregister the test message_type."""
        TestMessageBus._admin.deregister_message_type(message_types=\
            [TestMessageBus._message_type])
        message_type_list = TestMessageBus._admin.list_message_types()
        cls.assertTrue(cls, TestMessageBus._message_type not in \
            message_type_list)
        cls.assertFalse(cls, TestMessageBus._message_type in message_type_list)


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        TestMessageBus._cluster_conf_path = sys.argv.pop()
    unittest.main()
