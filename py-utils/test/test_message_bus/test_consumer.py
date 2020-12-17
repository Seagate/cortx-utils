# !/usr/bin/env python3
#
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
from cortx.utils.message_bus import MessageBus, MessageConsumer


class TestMessage(unittest.TestCase):
    """ Test MessageBus related functionality. """

    def test_receive(self):
        """ Test Receive Message. """
        message_bus = MessageBus()
        consumer = MessageConsumer(message_bus, consumer_id="sel", \
            consumer_group="sel", message_type=['Sel'], auto_ack=False, \
            offset='earliest')

        self.assertIsNotNone(consumer, "Consumer not found")
        messages = consumer.receive()
        self.assertIsNotNone(messages, "Messages not found")
        for message in messages:
            print(message)


if __name__ == '__main__':
    unittest.main()
