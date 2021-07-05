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

import os
import unittest

from cortx.utils.support import UtilsSupportBundle


class TestSupportBundle(unittest.TestCase):

    def test_support_bundle_a(self):
        """ Test by generating support tar in default location """
        UtilsSupportBundle.generate()
        status = os.path.exists("/tmp/cortx/support_bundle/py-utils.tar.gz")
        self.assertTrue(status)

    def test_support_bundle_b_custom_target_output(self):
        """ Test by generating support tar in custom location """
        UtilsSupportBundle.generate(target_path="/tmp/sbtest/out/")
        status = os.path.exists("/tmp/sbtest/out/py-utils.tar.gz")
        self.assertTrue(status)

    def test_support_bundle_c_wrong_target_output(self):
        """ Test by generating support tar in some random -,. location """
        UtilsSupportBundle.generate(target_path="-")
        status = os.path.exists("-/py-utils.tar.gz")
        self.assertTrue(status)


if __name__ == '__main__':
    """
    Firstly create the file and load sample json into it.
    Start test
    """
    unittest.main()
