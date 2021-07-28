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
import importlib
import inspect

from cortx.utils.errors import TestFailed


class TestRunner:
    """
    Loads tests according to various criteria and returns them wrapped
    in a TestSuite and displays results in textual form. It prints out the
    names of tests as they are run, errors as they occur, and a summary of
    the results at the end of the test run.
    """

    @staticmethod
    def _run_class_setup_method(test_class):
        """
        Runs class setup for test
        """
        for method_name, obj in inspect.getmembers(test_class):
            if inspect.ismethod(obj) and method_name.startswith('set'):
                setup_class = method_name
        try:
            class_setup = getattr(test_class(), setup_class)
            class_setup()
        except Exception as err:
            print("Class setup failed:",err)

    @staticmethod
    def _run_class_teardown_method(test_class):
        """
        Runs class teardown for test
        """
        for method_name, obj in inspect.getmembers(test_class):
            if inspect.ismethod(obj) and method_name.startswith('tear'):
                teardown_class = method_name
        try:
            class_teardown = getattr(test_class(), teardown_class)
            class_teardown()
        except Exception as err:
            print("Class teardown failed:",err)

    @staticmethod
    def _run_test_setup_method(test_class):
        """
        Runs test setup for test
        """
        for func_name, obj in inspect.getmembers(test_class):
            if inspect.isfunction(obj) and func_name.startswith('set'):
                setup_test = func_name
        try:
            test_setup = getattr(test_class(), setup_test)
            test_setup()
        except Exception as err:
            print("Test setup failed:",err)

    @staticmethod
    def _run_test_teardown_method(test_class):
        """
        Runs test teardown for test
        """
        for func_name, obj in inspect.getmembers(test_class):
            if inspect.isfunction(obj) and func_name.startswith('tear'):
                teardown_test = func_name
        try:
            test_teardown = getattr(test_class(), teardown_test)
            test_teardown()
        except Exception as err:
            print("Test teardown failed:",err)

    @staticmethod
    def get_tests_from_testname(ts):
        """
        Loads test based on class and test name
        """
        try:
            ts_module = importlib.import_module(ts.rsplit('.', 2)[0])
            class_name = ts.rsplit('.', 2)[1]
            tests = [ts.rsplit('.', 2)[2]]
            test_class = getattr(ts_module, class_name)
        except (ImportError, Exception) as err:
            print(err)
        return test_class, tests

    @staticmethod
    def get_tests_from_modules(ts):
        """
        load test from modules
        """
        test_classes = []
        tests = []
        try:
            ts_module = importlib.import_module(ts)
        except ImportError:
            print("Module doesn't exist")
        for _class_name, obj in inspect.getmembers(ts_module):
            if inspect.isclass(obj) and obj.__module__ == ts:
                test_classes.append(obj)
        for test_class in test_classes:
            for test_name, obj in inspect.getmembers(test_class):
                if inspect.isfunction(obj) and test_name.startswith('test_'):
                    tests.append(test_name)
        return test_class, tests

    @staticmethod
    def create_test_suite(argp):
        """
        Prepare testsuite to run the test, all or subset as
        per plan passed in command line args.
        """
        ts_list = []
        if argp.t is not None:
            if not os.path.exists(argp.t):
                raise TestFailed("Missing file: %s, Unable to run test plan."\
                    " Possibly invalid name. Check and confirm the plan name"\
                        " is correct" %argp.t)
            try:
                with open(argp.t) as f:
                    content = f.readlines()
                    for line in content:
                        if not line.startswith('#') and line != '\n':
                            ts_list.append(line.strip())
            except Exception as err:
                raise TestFailed("Can not open the file:" %err)
        else:
            # Below code returns a list of all files under test directory \
            # if plan file is not passed in command line args
            import cortx.utils.test as test_dir
            file_path = os.path.join(os.path.dirname(test_dir.__file__))
            for root, _directories, filenames in os.walk(file_path):
                for filename in filenames:
                    print("filename: %s" %filename)
                    if re.match(r'test_.*\.py$', filename):
                        file = os.path.join(root, filename).rsplit('.', 1)[0]\
                            .replace(file_path + "/", "").replace("/", ".")
                        ts_list.append(file)
        return ts_list

    @staticmethod
    def _test_report(ts_count, test_count, pass_count, fail_count, \
        total_start_time, result):
        """
        Prints summary of tests and testsuites ran
        """
        #View of consolidated test suite status
        print('\n' + '*'*120)
        print('{:90} {:10} {:10}'.format('TestSuites', 'Status', 'Duration(secs)'))
        print('*'*120)
        for k,v in result.items():
            print('{:90} {:10} {:10}s'.format(k, list(v.keys())[0], \
                int(list(v.values())[0])))

        # View of consolidated tests ran status
        total_duration = 0
        total_duration += time.time() - total_start_time
        print('\n'*2 + '*'*90)
        print("TestSuites: %s  Tests: %s  Passed: %s  Failed: %s  TimeTaken: %ds" \
            %(ts_count, test_count, pass_count, fail_count, total_duration))
        print('*'*90)

    @staticmethod
    def execute_tests(argp):
        """
        Runs the given tests and testsuites
        """
        result = {}
        ts_count = test_count = pass_count = fail_count = ts_duration = 0
        total_start_time = time.time()
        ts_list = TestRunner.create_test_suite(argp)

        print("\n********* Starting Test Execution *********")
        for ts in ts_list:
            ts_count += 1
            found_failed_test = False
            print("\n### Running Test Suite: %s ###" %ts)
            # Below code will differentiate whether to run single test
            # or all tests from module.
            if len(ts.split('.')) >= 3:
                # can be '== 4', if all tests were in respective directories
                # under test.
                test_class, tests = TestRunner.get_tests_from_testname(ts)
            else:
                test_class, tests = TestRunner.get_tests_from_modules(ts)
            # Actual test execution starts here
            ts_start_time = time.time()
            TestRunner._run_class_setup_method(test_class)
            for test in tests:
                test_count += 1
                try:
                    run_test = getattr(test_class(), test)
                    TestRunner._run_test_setup_method(test_class)
                    run_test()
                    print("TEST: %s: SUCCESS" %test)
                    pass_count += 1
                except (TestFailed, Exception) as test_error:
                    print("TEST: %s: FAILED" %test)
                    print("Traceback: %s" %test_error)
                    fail_count += 1
                    found_failed_test = True
                finally:
                    TestRunner._run_test_teardown_method(test_class)
            TestRunner._run_class_teardown_method(test_class)

            ts_duration = time.time() - ts_start_time
            if not found_failed_test:
                result.update({ts: {'Pass': ts_duration}})
            else:
                result.update({ts: {'Fail': ts_duration}})

        print("\n********* Test Execution Completed *********")
        TestRunner._test_report(ts_count, test_count, pass_count, fail_count, \
            total_start_time, result)
