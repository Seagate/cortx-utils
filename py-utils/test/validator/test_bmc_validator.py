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
import os

utils_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(utils_root)

from cortx.utils.validator.v_bmc import BmcV
from cortx.utils.validator.error import VError
from cortx.utils.validator.config import Bmc_V_Types as v_types

class TestBmcValidator(unittest.TestCase):
    """Test BMC related validations."""

    def test_accessibility_ok(self):
        """ Check BMC Accessibility """
        BmcV().validate(v_types.ACCESSIBLE.value, ['srvnode-1','srvnode-2'])

    def test_accessibility_no_args_error(self):
        """ Check 'accessible' validation type for no arguments """
        self.assertRaises(VError, BmcV().validate,
                          v_types.ACCESSIBLE.value,[])

    def test_accessibility_error(self):
        """ Check 'accessible' validation type for fake arguments """
        fake_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, BmcV().validate,
                          v_types.ACCESSIBLE.value, fake_hosts)

    def test_stonith_ok(self):
        """ Check Stonith configuration """
        cfg_args = ['srvnode-1', '192.168.12.123', 'admin', 'Admin!']
        BmcV().validate(v_types.STONITH.value, cfg_args)

    def test_stonith_no_args_error(self):
        """ Check 'stonith' validation type for no arguments """
        self.assertRaises(VError, BmcV().validate, v_types.STONITH.value,[])

    def test_stonith_less_args_error(self):
        """ Check 'stonith' validation type for less arguments """
        cfg_args = ['srvnode-1', '192.168.12.123', 'admin']
        self.assertRaises(VError, BmcV().validate,
                          v_types.STONITH.value,cfg_args)

    def test_stonith_more_args_error(self):
        """ Check 'stonith' validation type for more arguments """
        cfg_args = ['srvnode-1', '192.168.12.123', 'admin', 'Admin!', 'DummyData']
        self.assertRaises(VError, BmcV().validate,
                          v_types.STONITH.value, cfg_args)

    def test_incorrect_vtype(self):
        """ Check incorrect validation type """
        self.assertRaises(VError, BmcV().validate, 'dummy',[])

if __name__ == '__main__':
    unittest.main()
