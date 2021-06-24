#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

dir_path = os.path.dirname(os.path.abspath(__file__))


class TestSuite:
    """Create and run test suite"""
    
    def run_test_suite(self):
        """create and run complete test suite""" 
        loader = unittest.TestLoader()
        #Creates test suite
        test_suite = loader.discover(dir_path, pattern='test*.py', \
            top_level_dir=None)
        runner = unittest.TextTestRunner(verbosity=2)
        #Runs test suite
        runner.run(test_suite)
