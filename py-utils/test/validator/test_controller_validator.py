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

import sys
import os
import errno
import unittest

from cortx.utils import const
from cortx.utils.validator.v_controller import ControllerV
from cortx.utils.validator.error import VError

utils_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(utils_root)


class TestControllerV(unittest.TestCase):
    """ Test storage controller related validations. """

    IP = ""
    USERNAME = ""
    PASSWD = ""

    def setUp(self):
        """ Initialize controller validator. """
        self.cntrlr_validator = ControllerV()

    def test_accessibility_ok(self):
        """ Check primary & secondary controller are reachable. """
        self.cntrlr_validator.validate("accessible", [self.IP, self.USERNAME, self.PASSWD])

    def test_firmware_version_ok(self):
        """ Check controller bundle version. """
        mc_expected = ["GN265", "GN280"]
        self.cntrlr_validator.validate("firmware", [self.IP, self.USERNAME, self.PASSWD, mc_expected])

    def test_accessibility_no_args_error(self):
        """ Check 'accessible' validation type for no arguments. """
        self.assertRaises(VError, self.cntrlr_validator.validate, 'accessible', [])

    def test_incorrect_vtype(self):
        """ Check incorrect validation type. """
        self.assertRaises(VError, self.cntrlr_validator.validate, 'dummy', [])

    def test_accessibility_auth_error(self):
        """ Check 'accessible' validation type for invalid user access. """
        invalid_data = [self.IP, "tester007", "Tester!007"]
        self.assertRaises(VError, self.cntrlr_validator.validate, 'accessible', invalid_data)

    def test_accessibility_conn_error(self):
        """ Check 'accessible' validation type for invalid ip. """
        invalid_data = ["10.256.256.10", "tester007", "Tester!007"]
        self.assertRaises(VError, self.cntrlr_validator.validate, 'accessible', invalid_data)

    def test_unsupported_bundle(self):
        """ Check 'accessible' validation for an unsupported bundle version of controller. """
        mc_expected = ["GN000", "280GN"]
        self.assertRaises(VError, self.cntrlr_validator.validate, "firmware",\
            [self.IP, self.USERNAME, self.PASSWD, mc_expected])

    def test_web_service(self):
        # TODO: validate web service availability
        pass

    def tearDown(self):
        pass


if __name__ == '__main__':
    if len(sys.argv[1:]) < 3:
        raise Exception("Insufficient arguments. Test requires <ip> <username> <password>")
    TestControllerV.PASSWD = sys.argv.pop()
    TestControllerV.USERNAME = sys.argv.pop()
    TestControllerV.IP = sys.argv.pop()

    unittest.main()
