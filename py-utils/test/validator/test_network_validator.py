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

from cortx.utils.validator.error import VError
from cortx.utils.validator.v_network import NetworkV
import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestNetworkValidator(unittest.TestCase):
    """Test network related validations."""

    def test_network_connectivity(self):
        """Check IP connectivity failure."""

        fake_ip1 = '11.230.249.110'
        fake_ip2 = '12.230.249.110'
        self.assertRaises(VError, NetworkV().validate, [
                          'connectivity', fake_ip1, fake_ip2])


if __name__ == '__main__':
    unittest.main()
