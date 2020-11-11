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

    def test_hba_present(self):
        """Check HBA present """

        StorageV().validate('hba', ["lsi", 'srvnode-1'])

    def test_hba_provider(self):
        """Check HBA present """

        self.assertRaises(VError, StorageV().validate, 'hba',
                          ["abcd", 'srvnode-1'])

    def test_hba_not_present(self):
        """Check HBA not present """

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'hba',
                          ["lsi", dummy_hosts])

    def test_luns_accessible(self):
        """Check LUNs Accessible """

        StorageV().validate('luns', ["accessible", 'srvnode-1'])

    def test_luns_accessible_error(self):
        """Check LUNs accessible """

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'luns',
                          ["accessible", dummy_hosts])

    def test_luns_size(self):
        """Check LUNs Size """

        StorageV().validate('luns', ["size", 'srvnode-1'])

    def test_luns_size_error(self):
        """Check LUNs Ports """

        dummy_hosts = ['srv-1', 'srv-2']
        self.assertRaises(VError, StorageV().validate, 'luns',
                          ["size", dummy_hosts])

    def test_luns_wrongly_mapped(self):
        """Check LUNs mapping """

        self.assertRaises(VError, StorageV().validate, 'luns',
                          ["mapped", 'srvnode-1'])

    def test_luns_wrong_hosts(self):
        """Check LUNs mapping """

        self.assertRaises(VError, StorageV().validate, 'luns',
                          ["mapped", 'srvnode-1'])

    def test_lvm_error(self):
        """Check LVM not present."""

        self.assertRaises(VError, StorageV().validate, 'lvms',
                          ["srvnode-1", "srvnode-2"])


if __name__ == '__main__':
    unittest.main()
