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


class TestMessage(unittest.TestCase):
    """ Test MessageBus rest server functionality. """

    _base_url = 'http://127.0.0.1:28300/EventMessage/event'
    _component = 'cmp'
    _headers = {'content-type': 'application/json'}
    _bulk_count = 200
    _payload = {'component': 'cmp', 'source': 'H', 'module': 'mod', \
        'event_id': '500', 'severity': 'B', 'message_blob': 'This is alert'}

    def test_alert_send(self):
        """ Test send message """
        data = json.dumps(self._payload)
        response = requests.post(url=self._base_url, data=data, \
            headers=self._headers)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.status_code, 200)

    def test_alert_verify_receive(self):
        """ Test receive message """
        response = requests.get(self._base_url + '?component=' + \
            self._component)
        self.assertEqual(response.status_code, 200)
        alert = response.json()['alert']
        self.assertIs(type(alert), dict)

    def test_bulk_alert_send(self):
        """ Test bulk send alerts """
        for alert_count in range(0, self._bulk_count):
            self._payload['message_blob'] = f'This is alert {alert_count}'
            data = json.dumps(self._payload)
            response = requests.post(url=self._base_url, data=data, \
                headers=self._headers)
            self.assertEqual(response.json()['status'], 'success')
            self.assertEqual(response.status_code, 200)

    def test_bulk_verify_receive(self):
        """ Test bulk receive alerts """
        count = 0
        while True:
            response = requests.get(self._base_url + '?component=' + \
                self._component)
            self.assertEqual(response.status_code, 200)
            alert = response.json()['alert']
            if alert is None:
                break
            self.assertIs(type(alert), dict)
            count += 1
        self.assertEqual(count, self._bulk_count)

    def test_json_alert_send(self):
        """ Test send json as message description """
        self._payload['message_blob'] = json.dumps({'input': 'This is message'})
        data = json.dumps(self._payload)
        response = requests.post(url=self._base_url, data=data, \
            headers=self._headers)
        self.assertEqual(response.json()['status'], 'success')
        self.assertEqual(response.status_code, 200)

    def test_json_verify_receive(self):
        """ Test receive json as message description """
        response = requests.get(self._base_url + '?component=' + \
            self._component)
        self.assertEqual(response.status_code, 200)
        alert = response.json()['alert']
        self.assertIs(type(alert), dict)

    def test_validate_no_optional_params(self):
        """ Validate without optional params of send attributes """
        data = json.dumps(self._payload)

        send_response = requests.post(url=self._base_url, data=data, \
            headers=self._headers)
        self.assertEqual(send_response.json()['status'], 'success')
        self.assertEqual(send_response.status_code, 200)

        receive_response = requests.get(self._base_url + '?component=' + \
            self._component)
        self.assertEqual(receive_response.status_code, 200)
        alert = receive_response.json()['alert']

        self.assertEqual(alert['iem']['location']['site_id'], \
            alert['iem']['source']['site_id'])
        self.assertEqual(alert['iem']['location']['node_id'], \
            alert['iem']['source']['node_id'])
        self.assertEqual(alert['iem']['location']['rack_id'], \
            alert['iem']['source']['rack_id'])

    def test_validate_optional_params(self):
        """ Validate with optional params of send attributes """
        self._payload['problem_site_id'] = '2'
        self._payload['problem_rack_id'] = '6'
        self._payload['problem_node_id'] = '9'
        data = json.dumps(self._payload)

        send_response = requests.post(url=self._base_url, data=data, \
            headers=self._headers)
        self.assertEqual(send_response.json()['status'], 'success')
        self.assertEqual(send_response.status_code, 200)

        receive_response = requests.get(self._base_url + '?component=' + \
            self._component)
        self.assertEqual(receive_response.status_code, 200)
        alert = receive_response.json()['alert']

        self.assertNotEqual(alert['iem']['location']['site_id'], \
            alert['iem']['source']['site_id'])
        self.assertNotEqual(alert['iem']['location']['node_id'], \
            alert['iem']['source']['node_id'])
        self.assertNotEqual(alert['iem']['location']['rack_id'], \
            alert['iem']['source']['rack_id'])


if __name__ == '__main__':
    unittest.main()