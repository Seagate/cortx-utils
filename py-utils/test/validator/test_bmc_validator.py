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

import salt.client
import unittest
import errno
import sys
import os

utils_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(utils_root)

from cortx.utils import const
from cortx.utils.process import SimpleProcess
from cortx.utils.validator.v_bmc import BmcV
from cortx.utils.validator.error import VError
from cortx.utils.security.cipher import Cipher

class TestBmcValidator(unittest.TestCase):
    """Test BMC related validations."""

    def setUp(self):
        """Get bmc data on nodes in cluster"""
        self.bmc_data = dict()
        self.cluster_id = self.fetch_salt_data('grains.get', const.CLUSTER_ID)
        self.node_list = self.fetch_salt_data('pillar.get', 'cluster')['node_list']
        for node in self.node_list:
            node_bmc = self.fetch_salt_data('pillar.get', 'cluster')[node]['bmc']
            self.bmc_data.update({node: node_bmc})

    def fetch_salt_data(self, func, arg):
        """Get value for any required key"""
        result = salt.client.Caller().function(func, arg)
        if not result:
            raise VError(errno.EINVAL, f"No result found for '{arg}' in salt")
        return result

    def test_accessibility_ok(self):
        """ Check BMC accessibility for nodes in cluster"""
        for node in self.node_list:
            bmc_ip = self.bmc_data[node]['ip']
            bmc_user = self.bmc_data[node]['user']
            secret = self.bmc_data[node]['secret']
            key = Cipher.generate_key(self.cluster_id, 'cluster')
            bmc_passwd = Cipher.decrypt(key, secret.encode('ascii')).decode()
            BmcV().validate('accessible', node, bmc_ip, bmc_user, bmc_passwd)

    def test_accessibility_no_args_error(self):
        """ Check 'accessible' validation type for no arguments """
        self.assertRaises(VError, BmcV().validate, 'accessible', [])

    def test_accessibility_error_on_invalid_node(self):
        """ Check 'accessible' validation type for fake node argument """
        node = 'srvn-1'
        bmc_ip = self.bmc_data[node]['ip']
        user = self.bmc_data[node]['user']
        secret = self.bmc_data[node]['secret']
        key = Cipher.generate_key(self.cluster_id, 'cluster')
        passwd = Cipher.decrypt(key, secret.encode('ascii')).decode()
        self.assertRaises(VError, BmcV().validate, 'accessible', node, bmc_ip, user, passwd)

    def test_accessibility_error_on_invalid_auth(self):
        """ Check 'accessible' validation type for fake password argument """
        node = self.node_list[0]
        bmc_ip = self.bmc_data[node]['ip']
        user = self.bmc_data[node]['user']
        passwd = 'srv-1PASS'
        self.assertRaises(VError, BmcV().validate, 'accessible', node, bmc_ip, user, passwd)

    def test_stonith_ok(self):
        """ Check Stonith configuration """
        cfg_args = ['srvnode-1', '192.168.12.123', 'admin', 'Admin!']
        BmcV().validate('stonith', cfg_args)

    def test_stonith_no_args_error(self):
        """ Check 'stonith' validation type for no arguments """
        self.assertRaises(VError, BmcV().validate, 'stonith',[])

    def test_stonith_less_args_error(self):
        """ Check 'stonith' validation type for less arguments """
        cfg_args = ['srvnode-1', '192.168.12.123', 'admin']
        self.assertRaises(VError, BmcV().validate, 'stonith',cfg_args)

    def test_stonith_more_args_error(self):
        """ Check 'stonith' validation type for more arguments """
        cfg_args = ['srvnode-1', '192.168.12.123', 'admin', 'Admin!', 'DummyData']
        self.assertRaises(VError, BmcV().validate, 'stonith',cfg_args)

    def test_incorrect_vtype(self):
        """ Check incorrect validation type """
        self.assertRaises(VError, BmcV().validate, 'dummy',[])

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
