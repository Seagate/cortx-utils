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

import unittest
from cortx.utils.iem_framework import EventMessage
from cortx.utils.iem_framework.error import EventMessageError
from cortx.utils.conf_store import Conf


class TestMessage(unittest.TestCase):
    """Test EventMessage send and receive functionality."""
    _cluster_conf_path = ''
    _message_server_endpoints = ''
    _cluster_id = ''

    @classmethod
    def setUpClass(cls,  cluster_conf_path: str = 'yaml:///etc/cortx/cluster.conf'):
        if TestMessage._cluster_conf_path:
            cls.cluster_conf_path = TestMessage._cluster_conf_path
        else:
            cls.cluster_conf_path = cluster_conf_path
        Conf.load('config', cls.cluster_conf_path, skip_reload=True)
        TestMessage._cluster_id = Conf.get('config', 'cluster>id')
        TestMessage._message_server_endpoints = Conf.get('config',\
            'cortx>external>kafka>endpoints')

    def test_alert_send(self):
        """ Test send alerts """
        EventMessage.init(component='cmp', source='H', \
            cluster_id=TestMessage._cluster_id, \
            message_server_endpoints=TestMessage._message_server_endpoints)
        EventMessage.send(module='mod', event_id='500', severity='B', \
            message_blob='This is message')

    def test_alert_verify_receive(self):
        """ Test receive alerts """
        EventMessage.subscribe(component='cmp', \
            message_server_endpoints=TestMessage._message_server_endpoints)
        alert = EventMessage.receive()
        self.assertIs(type(alert), dict)

    def test_bulk_alert_send(self):
        """ Test bulk send alerts """
        EventMessage.init(component='cmp', source='H', \
            cluster_id=TestMessage._cluster_id, \
            message_server_endpoints=TestMessage._message_server_endpoints)
        for alert_count in range(0, 1000):
            EventMessage.send(module='mod', event_id='500', severity='B', \
                message_blob='test_bulk_message' + str(alert_count))

    def test_bulk_verify_receive(self):
        """ Test bulk receive alerts """
        EventMessage.subscribe(component='cmp', \
            message_server_endpoints=TestMessage._message_server_endpoints)
        count = 0
        while True:
            alert = EventMessage.receive()
            if alert is None:
                break
            self.assertIs(type(alert), dict)
            if 'test_bulk_message' in alert['iem']['contents']['message']:
                count += 1
        self.assertEqual(count, 1000)

    def test_alert_fail_receive(self):
        """ Receive message without subscribing """
        with self.assertRaises(EventMessageError):
            EventMessage.receive()

    def test_alert_fail_send(self):
        """ Send message without initialising """
        with self.assertRaises(EventMessageError):
            EventMessage.send(module='mod', event_id='500', severity='B', \
                message_blob='This is message')

    def test_receive_without_send(self):
        """ Receive message without send """
        EventMessage.subscribe(component='cmp', \
            message_server_endpoints=TestMessage._message_server_endpoints)
        alert = EventMessage.receive()
        self.assertIsNone(alert)

    def test_init_validation(self):
        """ Validate init attributes """
        with self.assertRaises(EventMessageError):
            EventMessage.init(component=None, source='H', \
                cluster_id=TestMessage._cluster_id, \
                message_server_endpoints=TestMessage._message_server_endpoints)
            EventMessage.init(component=None, source='I', \
                cluster_id=TestMessage._cluster_id, \
                message_server_endpoints=TestMessage._message_server_endpoints)

    def test_send_validation(self):
        """ Validate send attributes """
        with self.assertRaises(EventMessageError):
            EventMessage.send(module=None, event_id='500', severity='B', \
                message_blob='This is message')
            EventMessage.send(module='mod', event_id=None, severity='B', \
                message_blob='This is message')
            EventMessage.send(module='mod', event_id='500', severity='Z', \
                message_blob='This is message')
            EventMessage.send(module='mod', event_id='500', severity='Z', \
                message_blob=None)

    def test_subscribe_validation(self):
        with self.assertRaises(EventMessageError):
            EventMessage.subscribe(component=None, \
                message_server_endpoints=TestMessage._message_server_endpoints)

    def test_json_alert_send(self):
        """ Test send json as message description """
        EventMessage.init(component='cmp', source='H', \
            cluster_id=TestMessage._cluster_id, \
            message_server_endpoints=TestMessage._message_server_endpoints)
        EventMessage.send(module='mod', event_id='500', severity='B', \
            message_blob={'input': 'This is message'})

    def test_json_verify_receive(self):
        """ Test receive json as message description """
        EventMessage.subscribe(component='cmp', \
            message_server_endpoints=TestMessage._message_server_endpoints)
        alert = EventMessage.receive()
        self.assertIs(type(alert), dict)

    def test_validate_without_optional_params(self):
        """ Validate without optional params of send attributes """
        EventMessage.send(module='mod', event_id='500', severity='B', \
            message_blob={'input': 'This is message'})
        alert = EventMessage.receive()
        self.assertEqual(alert['iem']['location']['site_id'], \
            alert['iem']['source']['site_id'])
        self.assertEqual(alert['iem']['location']['node_id'], \
            alert['iem']['source']['node_id'])
        self.assertEqual(alert['iem']['location']['rack_id'], \
            alert['iem']['source']['rack_id'])

    def test_validate_with_optional_params(self):
        """ Validate with optional params of send attributes """
        EventMessage.send(module='mod', event_id='500', severity='B', \
            message_blob={'input': 'This is message'}, problem_site_id='2', \
            problem_rack_id='6', problem_node_id='9')
        alert = EventMessage.receive()
        self.assertNotEqual(alert['iem']['location']['site_id'], \
            alert['iem']['source']['site_id'])
        self.assertNotEqual(alert['iem']['location']['node_id'], \
            alert['iem']['source']['node_id'])
        self.assertNotEqual(alert['iem']['location']['rack_id'], \
            alert['iem']['source']['rack_id'])


if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        TestMessage._cluster_conf_path = sys.argv.pop()
    unittest.main()
