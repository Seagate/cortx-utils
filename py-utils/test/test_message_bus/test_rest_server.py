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
import requests
import json


class TestMessage(unittest.TestCase):
    """ Test MessageBus rest server functionality. """

    _base_url = 'http://127.0.0.1:28300/MessageBus/'
    _message_type = 'biggg'
    _consumer_group = 'connn'

    def test_post(self):
        """ Test send message. """
        url = self._base_url + self._message_type
        data = json.dumps({"messages": ["hello", "how are you"]})
        headers = {"content-type": "application/json"}
        response = requests.put(url=url, data=data, headers=headers)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        """ Test receive message. """
        response = requests.get(self._base_url + self._message_type + \
            '?consumer_group=' + self._consumer_group)
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
