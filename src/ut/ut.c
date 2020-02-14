/*
 * Filename: ut.h
 * Description: Unit Test Framework
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation, distribution
 * or disclosure of this code, for any reason, not expressly authorized is
 * prohibited. All other rights are expressly reserved by Seagate Technology, LLC.
 */
/******************************************************************************/

#include <errno.h>
#include "ut.h"

static int file_desc, saved_stdout, saved_stderr;

int ut_init(char * log_path)
{
	int rc = 0;

	file_desc = open(log_path, O_WRONLY | O_APPEND | O_CREAT, 0644);
	if (file_desc < 0) {
		rc = -errno;
		goto out;
	}
	fprintf(stdout,"Test results are logged to %s\n", log_path);

	saved_stdout = dup(STDOUT_FILENO);
	saved_stderr = dup(STDERR_FILENO);

        dup2(file_desc, STDOUT_FILENO);
	dup2(file_desc, STDERR_FILENO);

	time_t start_time;
	time(&start_time);

	fprintf(stdout, "\n\nStart time is %s\n", ctime(&start_time));

out:
	return rc;
}

void ut_fini(void)
{
	time_t finish_time;
	time(&finish_time);
	fprintf(stdout, "Finish time is %s\n", ctime(&finish_time));

	fflush(stdout);

	dup2(saved_stdout, STDOUT_FILENO);
	dup2(saved_stderr, STDERR_FILENO);

	close(file_desc);
}

int ut_run(struct test_case test_list[], int test_count)
{
	struct CMUnitTest  tests[MAX_TEST] = {{NULL}};

	int i;
	for(i = 0; i<test_count; i ++) {
		struct CMUnitTest temp = cmocka_unit_test(test_list[i].test_func);
		tests[i] = temp;
		tests[i].name = test_list[i].test_name;
	}

	return cmocka_run_group_tests(tests, NULL, NULL);
}

void ut_assert_true(int expression)
{
	assert_true(expression);
}

void ut_assert_false(int expression)
{
	assert_false(expression);
}

void ut_assert_null(void * pointer)
{
	assert_null(pointer);
}

void ut_assert_not_null(void * pointer)
{
	assert_non_null(pointer);
}

void ut_assert_int_equal(int a, int b)
{
	assert_int_equal(a, b);
}

void ut_assert_int_not_equal(int a, int b)
{
	assert_int_not_equal(a, b);
}

void ut_assert_string_equal(const char * a, const char * b)
{
	assert_string_equal(a, b);
}

void ut_assert_string_not_equal(const char * a, const char * b)
{
	assert_string_not_equal(a, b);
}
