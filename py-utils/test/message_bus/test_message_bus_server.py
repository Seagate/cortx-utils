#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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


import json
import unittest
import requests
from cortx.utils.message_bus import MessageBusAdmin


class TestMessage(unittest.TestCase):

    """Test MessageBus rest server functionality."""

    _base_url = 'http://127.0.0.1:28300/MessageBus/message/'
    _admin = MessageBusAdmin(admin_id='register')
    _message_type = 'test'
    _consumer_group = 'receive'

    @classmethod
    def setUpClass(cls):
        """Register the test message_type."""
        cls._admin.register_message_type(message_types= \
            [TestMessage._message_type], partitions=1)

    def test_post(self):
        """Test send message."""
        url = self._base_url + self._message_type
        data = json.dumps({'messages': ['hello', 'how are you']})
        headers = {'content-type': 'application/json'}
        response = requests.post(url=url, data=data, headers=headers)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        """Test receive message."""
        response = requests.get(self._base_url + self._message_type
            + '?consumer_group=' + self._consumer_group)
        self.assertEqual(response.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        """Deregister the test message_type."""
        cls._admin.deregister_message_type(message_types= \
            [TestMessage._message_type])
        message_type_list = TestMessage._admin.list_message_types()
        cls.assertTrue(cls, TestMessage._message_type not in \
            message_type_list)


if __name__ == '__main__':
    unittest.main()