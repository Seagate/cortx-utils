/*
 * Filename:    perf-manual-test.c
 * Description: This file implements several test cases for manual testing of
 *		performance-related interfaces.
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

/* Print tsdb output into stdout instead of using ADDB. */
#undef ENABLE_TSDB_ADDB
#define ENABLE_TSDB_PRINTF

#include "operation.h"
#include <assert.h>

static
void tsdb_run_manual_test(void)
{
	/* Test basic functions */
	{
		/* Expected result:
		 *	all the numbers appear on the screen
		 */
		(void) tsdb_init(true, true);
		TSDB_ADD(1, 2, 3);
		TSDB_ADD(1);
		TSDB_ADD(0xCAFE);
		TSDB_ADD(0xEFAC, UINT64_MAX, 0);
		TSDB_ADD(0, 1, 2, 3, 4, 5, 6, 7, 8, 9);
		tsdb_fini();
	}
	/* Test rt state */
	{
		/* Expected result:
		 *	all the numbers except 0xDEAD
		 *	appear on the screen
		 */
		(void) tsdb_init(true, false);
		TSDB_ADD(0xDEAD);
		tsdb_set_rt_state(true);
		TSDB_ADD(0xFF);
		tsdb_set_rt_state(false);
		TSDB_ADD(0xDEAD);
		tsdb_fini();
	}
	/* Test engine state */
	{
		/* Expected result:
		 *	all the numbers except 0xDEAD
		 *	appear on the screen
		 */
		(void) tsdb_init(false, false);
		TSDB_ADD(0xDEAD);
		tsdb_set_rt_state(true);
		TSDB_ADD(0xDEAD);
		tsdb_set_rt_state(false);
		TSDB_ADD(0xDEAD);
		tsdb_fini();

	}
}

/* list of tags of this test module */
enum {
	UT_CALL = 0x1,
	CALL_XA = 0xA,
	CALL_XB = 0xB,
	MAP_XID = 0xC,
};

struct modctx call_xm = MODCTX_INIT(TSDB_MOD_CUSTOM_START);
static void call_b(struct opstack *op, int arg)
{
	opstack_push(op, &call_xm, CALL_XB);
	printf("%s: called with %x\n", __FUNCTION__, arg);
	TSDB_ADD(0xCB1, opstack_head(op)->call_id, arg);
	TSDB_ADD(0xCB2, opstack_head(op)->call_id,
		 opstack_caller(op)->call_id);

	printf("current opcall: " OPCALL_DBG_FMT "\n",
	       OPCALL_DBG_P(opstack_curr(op)));
	printf("\tExpected(%d): f=%d, m=%d\n", __LINE__, CALL_XB,
	       TSDB_MOD_CUSTOM_START);

	printf("head opcall: " OPCALL_DBG_FMT "\n",
	       OPCALL_DBG_P(opstack_head(op)));
	printf("\tExpected(%d): f=%d, m=%d\n", __LINE__, UT_CALL,
	       TSDB_MOD_UT);

	opstack_map_head2external(op, MAP_XID, 0xFF);
	printf("\tExpected(%d): %x, %x, %x, %x, %x\n", __LINE__,
	       /* Action ID */
	       TSDB_MK_AID(TSDB_MOD_UT, UT_CALL),
	       /* PERFC subtag */
	       PERFC_MAP,
	       /* ID of the call */
	       1,
	       /* Map ID */
	       MAP_XID,
	       /* Foreign op ID */
	       0xFF);

	opstack_pop(op);
}

static void call_a(struct opstack *op, int arg)
{
	opstack_push(op, &call_xm, CALL_XA);
	call_b(op, arg);
	opstack_pop(op);
}

static
void opcall_run_manual_test(void)
{
	/* Test basic functions */
	{
		/* Expected result:
		 *	code compiles and executes successfully
		 *	no output (tsdb is not initialized)
		 */
		enum {
			MY_TAG_A = 0xA,
			MY_TAG_B = 0xB,
		};
		struct modctx m = MODCTX_INIT(TSDB_MOD_UT);
		struct opstack op = OPSTACK_INIT(&m, MY_TAG_A);
		opstack_push(&op, &m, MY_TAG_B);
		opstack_pop(&op);
		opstack_end(&op);
	}

	/* Test begin/end, push/pop */
	{
		/* Expected result:
		 *	code compiles and executes successfully
		 *	no output (tsdb is not initialized)
		 */
		enum {
			MY_TAG_A = 0xA,
			MY_TAG_B = 0xB,
		};
		struct modctx m = MODCTX_INIT(TSDB_MOD_UT);
		struct opstack op = OPSTACK_INIT_EMPTY();
		opstack_begin(&op, &m, MY_TAG_A);
		opstack_push(&op, &m, MY_TAG_B);
		opstack_pop(&op);
		opstack_end(&op);
	}

	/* Test calling another function */
	{
		tsdb_init(true, true);

		int i;
		struct modctx m = MODCTX_INIT(TSDB_MOD_UT);
		struct opstack op = OPSTACK_INIT_EMPTY();
		opstack_begin(&op, &m, UT_CALL);
		printf("\tExpected(%d) %x, %x, %x\n", __LINE__,
		       /* Action ID */
		       TSDB_MK_AID(TSDB_MOD_UT, UT_CALL),
		       /* 'b'egin subtag */
		       PERFC_EE_OP_BEGIN,
		       /* It is the first call */
		       1);
		for (i = 0; i < 3; i++) {
			call_a(&op, 0xF0 + i);
		}
		opstack_end(&op);
		printf("\tExpected(%d) %x, %x, %x\n", __LINE__,
		       /* Action ID */
		       TSDB_MK_AID(TSDB_MOD_UT, UT_CALL),
		       /* 'e'nd subtag */
		       PERFC_EE_OP_END,
		       /* It is still the first call */
		       1);

		printf("Expected AID: UTCALL=%x\n",
		       TSDB_MK_AID(TSDB_MOD_UT, UT_CALL));

		tsdb_fini();
	}

	/* Test expression-style definitions compilation */
	{
		/* Expected result:
		 *	code compiles and executes successfully
		 *	no output (tsdb is not initialized)
		 */
		struct modctx m = MODCTX_INIT(TSDB_MOD_UT);
		struct opstack op = OPSTACK_INIT_EMPTY();
		int rc;
		int val = 0xBAD;
		opstack_begin(&op, &m, UT_CALL);
		rc = val;
		val = opstack_end_rc(&op, rc);
		assert(rc == val);
		val = TSDB_ADD_EX(rc, 0);
		assert(rc == val);
	}
}

int main(void)
{
	printf("TSDB manual tests:\n");
	tsdb_run_manual_test();
	printf("OPCALL manual tests :\n");
	opcall_run_manual_test();
	return 0;
}
