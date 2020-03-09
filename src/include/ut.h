#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <error.h>
#include "common/log.h"
#define MAX_TEST 100
#define MAX_TEST_NAME 100

#define func_to_str(name) #name
#define ut_test_case(tests_func) { #tests_func, tests_func}
#define ut_assert_true(a) assert_true(a)
#define ut_assert_false(a) assert_false(a)
#define ut_assert_null(a) assert_null(a)
#define ut_assert_not_null(a) assert_not_null(a)
#define ut_assert_int_equal(a, b) assert_int_equal(a, b)
#define ut_assert_int_not_equal(a, b) assert_int_not_equal(a, b)
#define ut_assert_string_equal(a, b) assert_string_equal(a, b)
#define ut_assert_string_not_equal(a, b) assert_string_not_equal(a, b)

struct test_case {
	char test_name[MAX_TEST_NAME];
	void (*test_func) ();
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
 */
int ut_run(struct test_case[], int test_count);
