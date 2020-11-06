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

from cortx.utils.validator.v_network import NetworkV
from cortx.utils.validator.error import VError


class TestNetworkValidator(unittest.TestCase):
    """Test network related validations."""

    def test_connectivity_error(self):
        """Check IP connectivity failure."""

        fake_ip1 = '11.230.249.110'
        fake_ip2 = '12.230.249.110'
        self.assertRaises(VError, NetworkV().validate, 'connectivity',
                          [fake_ip1, fake_ip2])

    def test_connectivity_ok(self):
        ip1 = '8.8.8.8'
        NetworkV().validate('connectivity', [ip1])

    def test_host_connectivity_error(self):
        """Check host connectivity failure."""

        fake_host = 'www1.google.com'
        self.assertRaises(VError, NetworkV().validate, 'connectivity',
                          [fake_host])

    def test_host_connectivity_ok(self):
        host = 'localhost'
        NetworkV().validate('connectivity', [host])

    def test_nopasswordless_ssh(self):
        fake_hosts = ['srvnod-1', 'srvnod-2']
        args = ['root']
        args.extend(fake_hosts)
        self.assertRaises(VError, NetworkV().validate, 'passwordless',
                          args)

    def test_ofed_install_ok(self):
        """Check OFED Installed"""

        NetworkV().validate('drivers', ["mlnx-ofed", 'srvnode-1'])

    def test_ofed_driver_error(self):
        """Check OFED Installed - ERROR."""

        self.assertRaises(VError, NetworkV().validate, 'drivers',
                          ["abcd", 'srvnode-1'])

    def test_ofed_install_error(self):
        """Check OFED Installed - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, NetworkV().validate, 'drivers',
                          ["mlnx-ofed", dummy_hosts])

    def test_hca_present(self):
        """Check HCA present - CHECK."""

        NetworkV().validate('hca', ["mellanox", 'srvnode-1'])

    def test_hca_provider_error(self):
        """Check HCA present - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, NetworkV().validate, 'hca',
                          ["abcd", dummy_hosts])

    def test_hca_host_error(self):
        """Check HCA present - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, NetworkV().validate, 'hca',
                          ["mellanox", dummy_hosts])


if __name__ == '__main__':
    unittest.main()
