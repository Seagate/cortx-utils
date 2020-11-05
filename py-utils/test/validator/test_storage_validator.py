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

from cortx.utils.validator.v_storage import StorageV
from cortx.utils.validator.error import VError


class TestStorageValidator(unittest.TestCase):
    """Test Storage related validations."""

    def test_ofed_install_ok(self):
        """Check OFED Installed - CHECK."""

        rpm = "mlnx-ofed-all-4.7-3.2.9.0.rhel7.7.noarch"
        StorageV().validate('rpm', [rpm, 'srvnode-1'])

    def test_ofed_rpm_error(self):
        """Check OFED Installed - ERROR."""

        rpm = "dummy_rpm"
        self.assertRaises(VError, StorageV().validate, 'rpm', [rpm, 'srvnode-1'])

    def test_ofed_install_error(self):
        """Check OFED Installed - ERROR."""

        rpm = "mlnx-ofed-all-4.7-3.2.9.0.rhel7.7.noarch"
        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'rpm', [rpm, dummy_hosts])

    def test_hca_present(self):
        """Check HCA present - CHECK."""

        #hosts = ['localhost']
        StorageV().validate('hca', ['srvnode-1'])

    def test_hca_not_present(self):
        """Check HCA present - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'hca', dummy_hosts)

    def test_hca_ports_ok(self):
        """Check HCA Ports - CHECK."""

        StorageV().validate('hca_ports', ['srvnode-1'])

    def test_hca_ports_error(self):
        """Check HCA Ports - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'hca_ports', dummy_hosts)

    def test_lsb_hba_present(self):
        """Check LSB HBA present - CHECK."""

        StorageV().validate('lsb_hba', ['srvnode-1'])

    def test_lsb_hba_not_present(self):
        """Check LSB HBA present - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'lsb_hba', dummy_hosts)

    def test_lsb_hba_ports_ok(self):
        """Check LSB HBA Ports - CHECK."""

        StorageV().validate('lsb_hba_ports', ['srvnode-1'])

    def test_lsb_hba_ports_error(self):
        """Check LSB HBA Ports - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'lsb_hba_ports', dummy_hosts)

    def test_luns_ports_wrongly_mapped(self):
        """Check LUNs Ports - ERROR."""

        #StorageV().validate('vol_mapped', ['srvnode-1'])
        self.assertRaises(VError, StorageV().validate, 'volumes', ['srvnode-1'])

    def test_luns_ports_error(self):
        """Check LUNs Ports - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'volumes', dummy_hosts)

    def test_luns_inconsistent(self):
        """Check LUN inconsistent."""

        self.assertRaises(VError, StorageV().validate, 'luns',
                          ["srvnode-1", "srvnode-2"])

    def test_lvm_error(self):
        """Check LVM not present."""

        self.assertRaises(VError, StorageV().validate, 'lvms',
                          ["srvnode-1", "srvnode-2"])


if __name__ == '__main__':
    unittest.main()
