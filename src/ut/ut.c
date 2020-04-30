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

#include <debug.h>
#include "ut.h"

/* This macro enables self tests in eos-utils ut library.
 * The self test ensures that the API is stable enough to be
 * consumed by the users.
 * Disable the self test to speed up execution of each individual ut binary.
 */
#ifndef ENABLE_UT_SELF_TEST
#define ENABLE_UT_SELF_TEST 1
#endif

static struct collection_item *cfg_items = NULL;
static int file_desc, saved_stdout, saved_stderr;

static inline void ut_self_test(void)
{
	const bool always_true = true;
	const bool always_false = false;
	const void *always_nonull = (void*) ut_self_test;
	const int i1 = 1;
	const int i2 = 2;
	const char *str1 = "1";
	const char *str2 = "2";

	ut_assert_true(always_true);
	ut_assert_false(always_false);

	ut_assert_null(NULL);
	ut_assert_not_null(always_nonull);

	ut_assert_int_equal(i1, i1);
	ut_assert_int_equal(i1, 1);
	ut_assert_int_not_equal(i1, i2);
	ut_assert_int_not_equal(i1, 2);

	ut_assert_string_equal(str1, str1);
	ut_assert_string_equal(str1, "1");
	ut_assert_string_not_equal(str1, str2);
	ut_assert_string_not_equal(str1, "2");
}

int ut_init(char * log_path)
{
	#if ENABLE_UT_SELF_TEST
		ut_self_test();
	#endif

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

	if (cfg_items) {
		free_ini_config(cfg_items);
	}

	close(file_desc);
}

void ut_summary(int test_count, int test_failed)
{
	printf("Total tests  = %d\n", test_count);
	printf("Tests passed = %d\n", test_count-test_failed);
	printf("Tests failed = %d\n", test_failed);
}

int ut_run(struct test_case test_list[], int test_count, int (* setup)(), int (* teardown)())
{
	struct CMUnitTest  tests[MAX_TEST] = {{NULL}};

	int i;
	for(i = 0; i<test_count; i ++) {
		struct CMUnitTest temp = cmocka_unit_test_setup_teardown(test_list[i].test_func,
			test_list[i].setup_func, test_list[i].teardown_func);
		tests[i] = temp;
		tests[i].name = test_list[i].test_name;
	}

	return  cmocka_run_group_tests(tests, setup, teardown);
}

int ut_load_config(char *conf_file)
{
	int rc = 0;
	struct collection_item *errors = NULL;

	rc = config_from_file("libkvsns", conf_file, &cfg_items,
			      INI_STOP_ON_ERROR, &errors);
	if (rc != 0) {
		free_ini_config_errors(errors);
	}

	return rc;
}

char *ut_get_config(char *section, char *key, char *default_val)
{
	int rc = 0;
	char *tmp_val = strdup(default_val),
	     *value   = tmp_val;
	struct collection_item *item = NULL;

	dassert(cfg_items);

	rc = get_config_item(section, key, cfg_items, &item);
	if (rc != 0) {
		goto out;
	}

	value = get_string_config_value(item, NULL);
	if (value == NULL) {
		value = tmp_val;
	}

out:
	if (item) {
		free_ini_config_metadata(item);
	}

	return value;
}
