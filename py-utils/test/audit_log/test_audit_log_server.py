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


class TestAuditLog(unittest.TestCase):
    """Test AuditLog rest server functionality."""
    _base_url = 'http://0.0.0.0:28300/AuditLog/'

    def test_send_audit_log(self):
        """Send Audit log message."""
        url = self._base_url + 'message/'
        data = json.dumps({'messages': ['Hello', 'How are you?']})
        headers = {'content-type': 'application/json'}
        response = requests.post(url=url, data=data, headers=headers)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.status_code, 200)

    def test_send_webhook_info(self):
        """Send Audit log message."""
        url = self._base_url + 'webhook/'
        data = json.dumps({'external_server_info':\
            'external_server.com:port_no/AuditLog/webhook/'})
        headers = {'content-type': 'application/json'}
        response = requests.post(url=url, data=data, headers=headers)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()