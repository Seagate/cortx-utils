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
import sys
import argparse
import traceback

from cortx.test_framework.main import TestRunner

sys.path.append(os.path.join(os.path.dirname(__file__)))


def tmain():
    """Wrapper function to execute testsuites."""
    try:
        argParser = argparse.ArgumentParser(
            usage = "%(prog)s [-h] [-t]",
            formatter_class = argparse.RawDescriptionHelpFormatter)
        argParser.add_argument("-t",
                help="Enter path of plan file")
        args = argParser.parse_args()
    except Exception as e:
        print(e, traceback.format_exc())

    TestRunner.execute_tests(args)


if __name__ == '__main__':
    tmain()
