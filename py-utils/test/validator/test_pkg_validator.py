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
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.validator.error import VError

class TestRpmValidator(unittest.TestCase):
    """Test rpm related validations."""

    pkg = ['openssl']
    # host = 'localhost'

    def test_rpm_installed(self):
        """Check if rpm pkg installed."""
        PkgV().validate('rpms', self.pkg)

    def test_pip3_installed(self):
        """Check if pip3 pkg installed."""
        try:
            pkg = ['toml']
            PkgV().validate('pip3s', pkg)
        except Exception as e:
            self.fail("{}".format(e))

    # def test_remote_rpm_installed(self):
    #     """Check if rpm pkg installed."""
    #     PkgV().validate('rpms', self.pkg, self.host)

    # def test_remote_pip3_installed(self):
    #     """Check if pip3 pkg installed."""
    #     pkg = ['toml']
    #     PkgV().validate('pip3s', pkg, self.host)

    def test_neg_rpm_installed(self):
        """Check if neagtive rpm pkg installed."""
        neg_pkg = ['lvm2-2.02.186-7.el7']
        self.assertRaises(VError, PkgV().validate, 'rpms', neg_pkg)


if __name__ == '__main__':
    unittest.main()
