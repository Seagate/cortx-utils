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
from cortx.utils.message_bus import MessageBus, MessageBusAdmin


class TestMessage(unittest.TestCase):
    """ Test MessageBus related functionality """

    message_bus = MessageBus()

    message_type = 'test_topic'
    partition = 10
    _input = {message_type: partition}

    def test_list_message_type(self):
        """ Test list message type API """
        admin = MessageBusAdmin(TestMessage.message_bus, admin_id='admin')
        admin.register_message_type(message_types=[TestMessage.message_type], \
            partitions=TestMessage.partition)
        m_type_partitions = admin.list_message_types()
        self.assertTrue(set(TestMessage._input.items()).issubset\
            (set(m_type_partitions.items())))


if __name__ == '__main__':
    unittest.main()