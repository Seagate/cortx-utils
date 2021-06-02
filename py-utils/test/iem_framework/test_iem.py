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
from cortx.utils.message_bus.error import MessageBusError


class TestMessage(unittest.TestCase):
    """Test EventMessage send and receive functionality."""

    def test_alert_send(self):
        """ Test send alerts """
        EventMessage.init(component='cmp', source='H')
        EventMessage.send(module='mod', event_id='500', severity='B', \
            message='This is message')

    def test_alert_verify_receive(self):
        """ Test receive alerts """
        EventMessage.subscribe(component='cmp')
        alert = EventMessage.receive()
        self.assertIs(type(alert), dict)

    def test_bulk_alert_send(self):
        """ Test bulk send alerts """
        EventMessage.init(component='cmp', source='H')
        for alert_count in range(0, 1000):
            EventMessage.send(module='mod', event_id='500', severity='B', \
                message='This is message' + str(alert_count))

    def test_bulk_verify_receive(self):
        """ Test bulk receive alerts """
        EventMessage.subscribe(component='cmp')
        count = 0
        while True:
            alert = EventMessage.receive()
            if alert is None:
                break
            self.assertIs(type(alert), dict)
            count += 1
        self.assertEqual(count, 1000)

    def test_alert_fail_receive(self):
        """ Receive message init """
        with self.assertRaises(AttributeError):
            EventMessage.receive()

    def test_alert_fail_send(self):
        """ Send message with subscribe """
        with self.assertRaises(AttributeError):
            EventMessage.send(module='mod', event_id='500', severity='B', \
                message='This is message')

    def test_receive_without_send(self):
        """ Receive message without send """
        EventMessage.subscribe(component='cmp')
        alert = EventMessage.receive()
        self.assertIsNone(alert)

    def test_init_validation(self):
        """ Validate init attributes """
        with self.assertRaises(EventMessageError):
            EventMessage.init(component=None, source='H')
            EventMessage.init(component='cmp', source='I')

    def test_send_validation(self):
        """ Validate send attributes """
        with self.assertRaises(EventMessageError):
            EventMessage.send(module=None, event_id='500', severity='B', \
                message='This is message')
            EventMessage.send(module='mod', event_id=None, severity='B', \
                message='This is message')
            EventMessage.send(module='mod', event_id='500', severity='Z', \
                message='This is message')
            EventMessage.send(module='mod', event_id='500', severity='Z', \
                message=None)

    def test_json_alert_send(self):
        """ Test send json as message description """
        EventMessage.init(component='cmp', source='H')
        EventMessage.send(module='mod', event_id='500', severity='B', \
            message={'input': 'This is message'})

    def test_json_verify_receive(self):
        """ Test receive json as message description """
        EventMessage.subscribe(component='cmp')
        alert = EventMessage.receive()
        self.assertIs(type(alert), dict)


if __name__ == '__main__':
    unittest.main()