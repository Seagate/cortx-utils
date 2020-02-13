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

/**
 * Assert that the given expression ins true.
 * The function prints an error message to standard error and terminates
 * if expression is false.
 *
 * @param[in] expression - The expression to evaluate.
 */
void ut_assert_true(int expression);

/**
 * Assert that the given expression is false.
 * The function prints an error message to standard error and terminates
 * if expression is true.
 *
 * @param[in] expression - The expression to evaluate.
 */
void ut_assert_false(int expression);

/**
 * Assert that the given pointer is NULL.
 * The function prints an error message to standard error and terminates
 * if pointer is non-NULL.
 *
 * @param[in] pointer - The pointer to evaluate.
 */
void ut_assert_null(void * pointer);

/**
 * Assert that the given pointer is not NULL.
 * The function prints an error message to standard error and terminates
 * if pointer is NULL.
 *
 * @param[in] pointer - The pointer to evaluate.
 */
void ut_assert_not_null(void * pointer);


/**
 * Assert that the two given integers are equal.
 * The function prints an error message to standard error and terminates
 * if integers are not equal
 *
 * @param[in] a - The first integer to compare.
 * @param[in] b - The integer to compare against the first one.
 */
void ut_assert_int_equal(int a, int b);

/**
 * Assert that the two given integers are equal.
 * The function prints an error message to standard error and terminates
 * if integers are equal
 *
 * @param[in] a - The first integer to compare.
 * @param[in] b - The integer to compare against the first one.
 */
void ut_assert_int_not_equal(int a, int b);

/**
 * Assert that the two given integers are equal.
 * The function prints an error message to standard error and terminates
 * if strings are not equal
 *
 * @param[in] a - The string to check.
 * @param[in] b - The other string to compare.
 */
void ut_assert_string_equal(const char *a, const char *b);

/**
 * Assert that the two given integers are equal.
 * The function prints an error message to standard error and terminates
 * if strings are equal
 *
 * @param[in] a - The string to check.
 * @param[in] b - The other string to compare.
 */
void ut_assert_string_not_equal(const char *a, const char *b);
