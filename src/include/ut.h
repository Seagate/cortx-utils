/*
 * Filename: ut.h
 * Description: Headers for ut framework.
 *
 * Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published
 * by the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU Affero General Public License for more details.
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 * For any questions about this software or licensing,
 * please email opensource@seagate.com or cortx-questions@seagate.com. 
 */

#include <stdio.h>
#include <setjmp.h> /* jmp_buf */
#include <cmocka.h> /* cmocka */
#include <fcntl.h> /* O_WRONLY */
#include <unistd.h> /* STDOUT_FILENO */
#include <time.h> /* time_t */
#include <errno.h> /* errno */
#include <stdbool.h> /* bool */
#include <ini_config.h> /* config_from_file */
#include <string.h> /* strcmp */
#include <stdlib.h> /* free */
#include "common/log.h"
#define MAX_TEST 100
#define MAX_TEST_NAME 100

#define func_to_str(name) #name
#define ut_test_case(tests_func, setup_func, teardown_func) { #tests_func, tests_func, setup_func, teardown_func}
#define ut_assert_true(a) assert_true(a)
#define ut_assert_false(a) assert_false(a)
#define ut_assert_null(a) assert_null(a)
#define ut_assert_not_null(a) assert_non_null(a)
#define ut_assert_int_equal(a, b) assert_int_equal(a, b)
#define ut_assert_int_not_equal(a, b) assert_int_not_equal(a, b)
#define ut_assert_string_equal(a, b) assert_string_equal(a, b)
#define ut_assert_string_not_equal(a, b) assert_string_not_equal(a, b)

struct test_case {
	char test_name[MAX_TEST_NAME];
	void (*test_func) ();
	int (*setup_func) ();
	int (*teardown_func) ();
};

/**
 * Required initialization for UT
 * @param[in] log_path - File to log test rsults
 * @param[out] - Returns 0 of success, or errno if fails
 */
int ut_init(char * log_path);

/**
 * Required finish for UT
 */
void ut_fini();

/**
 * Runs tests passed funct_list.
 * Returns number of tests failed.
 * @param[in] test_case - Array of test cases
 * @param[in] test_cnt - count of tests.
 * @param[in] setup - Group setup function
 * @param[in] teardown - Group teardown function
 */
int ut_run(struct test_case[], int test_count, int (* setup)(), int (* teardown)());

/**
 * Prints summary of tests group.
 * @param[in] test_count - Total number tests
 * @param[in] test_failed - Number of tests failed
 */
void ut_summary(int test_count, int test_failed);

/**
 * Load UT config file.
 * @param[in] conf_file - UT conf file to be parsed.
 * @param[out] rc - 0 on sucess otherwise non-zero
 */
int ut_load_config(char *conf_file);

/**
 * Gets config from UT config file.
 * @param[in] section - Name of section in config to be parsed.
 * @param[in] key - name of attribute whose value is returned
 * @param[in] default_val -Default value of atribute.
 * @param[out] - Value of given attribute is returned. Return def_value
 * 		 in case of any failure
 */ 
char *ut_get_config(char *section, char *key, char * default_val);
