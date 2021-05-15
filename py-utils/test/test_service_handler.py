#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import sys
import os
import unittest

from cortx.utils.service.service_handler import Service

utils_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(utils_root)

class TestSystemHandler(unittest.TestCase):
    _service_name = 'rsyslog.service'

    def setUp(self):
        self.service_obj = Service(TestSystemHandler._service_name)

    def test_start(self):
        self.service_obj.start()
        service_state = self.test_get_state()
        self.assertEqual(service_state.state,'active')
        self.assertEqual(service_state.substate,'running')

    def test_stop(self):
        self.service_obj.stop()
        service_state = self.test_get_state()
        self.assertEqual(service_state.state,'inactive')
        self.assertEqual(service_state.substate,'dead')

    def test_restart(self):
        self.service_obj.restart()
        service_state = self.test_get_state()
        self.assertEqual(service_state.state,'active')
        self.assertEqual(service_state.substate,'running')

    def test_enable(self):
        self.service_obj.enable()
        is_enable = self.test_is_enabled()
        self.assertTrue(is_enable)

    def test_disable(self):
        self.service_obj.disable()
        is_enable = self.test_is_enabled()
        self.assertFalse(is_enable)

    def test_get_state(self):
        return self.service_obj.get_state()
    
    def test_is_enabled(self):
        return self.service_obj.is_enabled()

if __name__ == '__main__':
    unittest.main()