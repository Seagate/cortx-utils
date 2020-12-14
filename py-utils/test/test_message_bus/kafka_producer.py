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
import sys
sys.path.insert(1, '../../')
from cortx.utils.message_bus import MessageBus, MessageProducer, MessageConsumer

class TestMessage(unittest.TestCase):
    """Test MessageBus related functionality."""

    def test_send(self):
        """Test Send Message."""
        message_bus = MessageBus()
        producer = MessageProducer(message_bus, producer_id="sspl_sensor", message_type="Alert")
        self.assertIsNotNone(producer, "Producer not found")
        messages = ["This is message1", "This is message2"]
        self.assertIsInstance(messages, list)
        producer.send(messages)


if __name__ == '__main__':
    unittest.main()
