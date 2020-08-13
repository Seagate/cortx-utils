/*
 * Filename: fault-test.c
 * Description: Test script for fault framework.
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
#include <stdlib.h>
#include <fault.h>

#define REPEAT_START	2
#define REPEAT_END	5

#define SKIP_START	2
#define SKIP_END	5

#define TIME		2

#define PROBABILITY	50

void test_fault_once(void)
{
	int rc = 0;
	fault_id_t fp_id;

	fprintf(stdout, "Running Test : FAULT ONCE... ");

	rc = FP_ENABLED("pretend_failure", FP_ONCE(1));
	assert(rc == 0);

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not enabled. */

	// Enable fault point.
	fault_enable(&fp_id);

	rc = fault_enabled(&fp_id);
	assert(rc == 1); /* Fault is enabled. */ 

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* FP_ONCE should be enabled once. */ 

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

void test_fault_always(void)
{
	int rc = 0;
	fault_id_t fp_id;

	fprintf(stdout, "Running Test : FAULT ALWAYS... ");

	rc = FP_ENABLED("pretend_failure", FP_ALWAYS());
	assert(rc == 0);

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not enabled. */

	// Enable fault point.
	fault_enable(&fp_id);

	rc = fault_enabled(&fp_id);
	assert(rc == 1); /* Fault is enabled. */ 

	rc = fault_enabled(&fp_id);
	assert(rc == 1); /* FP_ALWAYS should be active until get's disabled. */ 

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

void test_fault_repeat(void)
{
	int rc = 0;
	int i;
	fault_id_t fp_id;

	fprintf(stdout, "Running Test : FAULT REPEAT... ");

	rc = FP_ENABLED("pretend_failure", FP_REPEAT(REPEAT_START, REPEAT_END));
	assert(rc == 0);

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not enabled. */

	// Enable fault point.
	fault_enable(&fp_id);

	for (i = REPEAT_START; i < REPEAT_END; i++) {
		rc = fault_enabled(&fp_id);
		assert(rc == 1); /* Fault is enabled. */
	}

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* FP_REPEAT should NOT be active beyond REPEAT_END. */ 

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

void test_fault_skip(void)
{
	int rc = 0;
	int i;
	fault_id_t fp_id;

	fprintf(stdout, "Running Test : FAULT SKIP... ");
	
	rc = FP_ENABLED("pretend_failure", FP_SKIP(SKIP_START, SKIP_END));
	assert(rc == 0);

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not enabled. */

	// Enable fault point.
	fault_enable(&fp_id);

	for (i = SKIP_START; i < SKIP_END; i++) {
		rc = fault_enabled(&fp_id);
		assert(rc == 0); /** FP_SKIP should NOT be active in between
				  *  SKIP_START and SKIP_END.
				  */
	}

	rc = fault_enabled(&fp_id);
	assert(rc == 1); 

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

void test_fault_delay(void)
{
	int rc = 0;
	fault_id_t fp_id;

	fprintf(stdout, "Running Test : FAULT DELAY... ");
	
	rc = FP_ENABLED("pretend_failure", FP_DELAY(TIME));
	assert(rc == 0);

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not enabled. */

	// Enable fault point.
	fault_enable(&fp_id);

	rc = fault_enabled(&fp_id);
	assert(rc == 1); 

	rc = fault_enabled(&fp_id);
	assert(rc == 1);

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

typedef struct user_func_data {
	int data;
} user_func_data_t;

int user_func_cb(void *cb_data)
{
	user_func_data_t *ufd = (user_func_data_t *)cb_data;
	
	return (ufd->data == 1);
}

void test_fault_user_func(void)
{

	int rc = 0;
	fault_id_t fp_id;
#if FAULT_INJECT
	user_func_data_t ufd;
	user_func_data_t *ptr_ufd;

	ufd.data = 1;
	ptr_ufd = &ufd;
#endif
	fprintf(stdout, "Running Test : FAULT USER_FUNC... ");

	rc = FP_ENABLED("pretend_failure", FP_USER_FUNC(user_func_cb, ptr_ufd));
	assert(rc == 0);

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not enabled. */

	// Enable fault point.
	fault_enable(&fp_id);

	rc = fault_enabled(&fp_id);
	assert(rc == 1); 

	rc = fault_enabled(&fp_id);
	assert(rc == 1);

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

void test_fault_random(void)
{
	int rc = 0;
	int hit_count = 0;
	fault_id_t fp_id;

	fprintf(stdout, "Running Test : FAULT RANDOM... ");
	
	rc = FP_ENABLED("pretend_failure", FP_RANDOM(PROBABILITY));
	assert(rc == 0);

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not enabled. */

	// Enable fault point.
	fault_enable(&fp_id);

	do {
		rc = fault_enabled(&fp_id);
		if (rc) {
			break;
		}
		// It's a random probability.
	} while(++hit_count < 100);

	assert(rc == 1);

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

void test_fault_enable_first(void)
{
	int rc = 0;
	fault_id_t fp_id;

	fprintf(stdout, "Running Test : ENABLE FIRST... ");

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	// Enable fault point.
	fault_enable(&fp_id);
	
	rc = FP_ENABLED("pretend_failure", FP_ONCE(1));
	assert(rc == 1);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active. */

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	fprintf(stdout, "[OK]\n");
}

void test_fault_enable_disable_enable(void)
{
	int rc = 0;
	fault_id_t fp_id;
	fprintf(stdout, "Running Test : ENABLE DISABLE ENABLE... ");

	fp_id.fpi_func = __func__;
	fp_id.fpi_tag = "pretend_failure";

	rc = FP_ENABLED("pretend_failure", FP_ALWAYS());
	assert(rc == 0);
	
	// Enable fault point.
	fault_enable(&fp_id);

	rc = fault_enabled(&fp_id);
	assert(rc == 1); /* Fault is active. */

	// Disable fault point.
	fault_disable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 0); /* Fault is not active */
	
	// Enable fault point.
	fault_enable(&fp_id);
	
	rc = fault_enabled(&fp_id);
	assert(rc == 1); /* Fault is active. */

	fprintf(stdout, "[OK]\n");
}

int main(int argc , char *argv[])
{
	// Init fault
	fault_init();

	test_fault_once();
	test_fault_always();
	test_fault_repeat();
	test_fault_skip();
	test_fault_delay();
	test_fault_user_func();
	test_fault_random();
	test_fault_enable_first();
	test_fault_enable_disable_enable();

	// Cleanup fault
	fault_cleanup();
	return 0;
}
