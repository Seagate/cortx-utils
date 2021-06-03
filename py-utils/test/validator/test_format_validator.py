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
from cortx.utils.validator.v_format  import FormatV
from cortx.utils.validator.error import VError

class TestFormatValidator(unittest.TestCase):

    def test_positive_int(self):
        self.assertIsNone(FormatV().validate("positive_int", 1))

    def test_negative_int(self):
        self.assertRaises(VError, FormatV().validate, "positive_int", -1)

    def test_char(self):
        self.assertRaises(VError, FormatV().validate, "positive_int", 'x')

    def test_file_format(self):
        self.assertIsNone(FormatV().validate("file_format", "/etc/hosts"))

    def test_incorrect_file_format(self):
        self.assertRaises(VError, FormatV().validate, "file_format", "../README.md")

if __name__ == '__main__':
    unittest.main()