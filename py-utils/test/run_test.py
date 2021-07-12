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
import re
import time
import argparse
import traceback


result = {}

def main(argp):
    """ Prepare testsuite to run the test, all or subset as \
        per plan passed in command line args """
    ts_list = []
    if argp.t is not None:
        if not os.path.exists(argp.t):
            raise TestFailed("Missing file %s , Unable to run test plan. \
                Possibly invalid name. Check and confirm the plan name is \
                    correct" %argp.t)
        with open(argp.t) as f:
            content = f.readlines()
            for x in content:
                if not x.startswith('#'):
                    ts_list.append(x.strip())
    else:
        file_path = os.path.dirname(os.path.realpath(__file__))
        for root, _directories, filenames in os.walk(file_path):
            for filename in filenames:
                print("filename: %s" %filename)
                if re.match(r'test_.*\.py$', filename):
                    file = os.path.join(root, filename).rsplit('.', 1)[0]\
                         .replace(file_path + "/", "").replace("/", ".")
                    ts_list.append(file)

    ts_count = test_count = pass_count = fail_count = 0
    ts_start_time = time.time()

    for ts in ts_list:
        print("\n###### Test Suite: %s ######" %ts)
        ts_count += 1
        ts_module = __import__(ts, fromlist=[ts])
        # Actual test execution
        found_failed_test = False
        duration = 0
        for test in ts_module.test_list:
            if (test.__name__).startswith('test_'):
                test_count += 1
            try:
                start_time = time.time()
                test()
                duration += time.time() - start_time
                if (test.__name__).startswith('test_'):
                    print("%s:%s: SUCCESS (Time: %ds)" \
                        %(ts, test.__name__, duration))
                    pass_count += 1
            except (TestFailed, Exception) as e:
                if (test.__name__).startswith('test_'):
                    print("%s:%s: FAILED #@#@#@#" %(ts, test.__name__))
                    print("    %s\n" %e)
                    fail_count += 1
                found_failed_test = True
        if not found_failed_test:
            result.update({ts: {'Pass': duration}})
        else:
            result.update({ts: {'Fail': duration}})

    # View of consolidated test suite status
    print('\n' + '*'*90)
    print('{:60} {:10} {:10}'.format('TestSuite', 'Status', 'Duration(secs)'))
    print('*'*90)
    for k,v in result.items():
        print('{:60} {:10} {:10}s'.format(k, list(v.keys())[0], \
            int(list(v.values())[0])))

    # View of consolidated tests run status
    duration = time.time() - ts_start_time
    print('\n'*2 + '*'*90)
    print("TestSuite: %s  Tests: %s  Passed: %s  Failed: %s  TimeTaken: %ds" \
        %(ts_count, test_count, pass_count, fail_count, duration))
    print('*'*90)

if __name__ == '__main__':
    from cortx.utils.errors import TestFailed
    try:
        argParser = argparse.ArgumentParser(
            usage = "%(prog)s [-h] [-t]",
            formatter_class = argparse.RawDescriptionHelpFormatter)
        argParser.add_argument("-t",
                help="Enter path of plan file")
        args = argParser.parse_args()

        main(args)
    except Exception as e:
        print(e, traceback.format_exc())
