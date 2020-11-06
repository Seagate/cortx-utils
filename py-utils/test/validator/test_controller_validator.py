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
import errno
import unittest
import salt.client

from cortx.utils import const
from cortx.validator.error import VError
from cortx.utils.security.cipher import Cipher
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.validator.v_controller import ControllerV

utils_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(utils_root)


class TestControllerV(unittest.TestCase):
    """Test storage contoller related validations"""

    def setUp(self):
        """Get primary and secondary MC of storage controller"""
        self.cluster_id = self.fetch_salt_data('grains.get', const.CLUSTER_ID)
        self.enclosure_data = self.fetch_salt_data('pillar.get', const.STORAGE_ENCLOSURE)
        self.primary_mc = self.enclosure_data['controller']['primary_mc']['ip']
        self.secondary_mc = self.enclosure_data['controller']['secondary_mc']['ip']

    @staticmethod
    def fetch_salt_data(func, arg):
        """Get value for any required key from salt"""
        result = salt.client.Caller().function(func, arg)
        if not result:
            raise VError(errno.EINVAL, "No result found for '%s'" % arg)
        return result

    def __fetch_username_password_from_salt(self):
        """Get valid username and password from salt"""
        username = self.enclosure_data['controller']['user']
        secret = self.enclosure_data['controller']['secret']
        key = Cipher.generate_key(self.cluster_id, const.STORAGE_ENCLOSURE)
        password = Cipher.decrypt(key, secret.encode('ascii')).decode()
        return username, password

    def test_controller_connectivity_ok(self):
        """Validate primary & secondary IP are rreachable"""
        NetworkV().validate('connectivity', [self.primary_mc])
        NetworkV().validate('connectivity', [self.secondary_mc])

    def test_accessibility_ok(self):
        """ Check primary & secondary controller consol accessibility"""
        user, passwd = self.__fetch_username_password_from_salt()
        validator = ControllerV()
        validator.mc_supported = ["GN265", "GN280"]
        validator.validate("accessible", [self.primary_mc, user, passwd])
        validator.validate("accessible", [self.secondary_mc, user, passwd])

    def test_accessibility_no_args_error(self):
        """ Check 'accessible' validation type for no arguments """
        self.assertRaises(VError, ControllerV().validate, 'accessible', [])

    def test_accessibility_auth_error(self):
        """ Check 'accessible' validation type for invalid user access"""
        invalid_data = [self.primary_mc, "tester007", "Tester!007"]
        self.assertRaises(VError, ControllerV().validate, 'accessible', invalid_data)

    def test_accessibility_conn_error(self):
        """ Check 'accessible' validation type for unreachable ip"""
        invalid_data = ["188.124.124.78", "tester007", "Tester!007"]
        self.assertRaises(VError, ControllerV().validate, 'accessible', invalid_data)

    def test_unsupported_bundle(self):
        """ Check 'accessible' validation for an unsupported bundle version of controller"""
        user, passwd = self.__fetch_username_password_from_salt()
        validator = ControllerV()
        validator.mc_supported = ["GN000", "280GN"]
        validator.validate("accessible", [self.primary_mc, user, passwd])

    def test_web_service(self):
        # TODO: validate web service availability
        pass

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
