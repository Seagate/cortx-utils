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


    def test_luns_present(self):
        """Check LUNs present - CHECK."""

        StorageV().validate('luns_accessible', ['srvnode-1'])

    def test_luns_not_present(self):
        """Check LUNs present - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'luns_accessible', dummy_hosts)


    def test_luns_ports_wrongly_mapped(self):
        """Check LUNs Ports - ERROR."""

        self.assertRaises(VError, StorageV().validate, 'volumes_mapped', ['srvnode-1'])

    def test_luns_ports_error(self):
        """Check LUNs Ports - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'volumes_mapped', dummy_hosts)


    def test_lvm_size_ok(self):
        """Check LVM size - CHECK."""

        StorageV().validate('lvm_size', ['srvnode-1'])

    def test_lvm_size_error(self):
        """Check LVM size - ERROR."""

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'lvm_size', dummy_hosts)

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
