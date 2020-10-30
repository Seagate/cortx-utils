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

from cortx.utils.validator.v_storage import StorageV
from cortx.utils.validator.error import VError


class TestStorageValidator(unittest.TestCase):
    """Test storage related validations."""

    def test_luns_inconsistent(self):
        """Check LUN inconsistent."""

        self.assertRaises(VError, StorageV().validate, 'luns_check',
                          ["srvnode-1", "srvnode-2"])

    def test_lvm_error(self):
        """Check LVM not present."""

        self.assertRaises(VError, StorageV().validate, 'lvms_check',
                          ["srvnode-1", "srvnode-2"])


if __name__ == '__main__':
    unittest.main()
