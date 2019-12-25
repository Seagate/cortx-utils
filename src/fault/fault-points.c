/**
 * Filename: fault-points.c
 * Description: Internal definations for fault framework.
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation, distribution
 * or disclosure of this code, for any reason, not expressly authorized is
 * prohibited. All other rights are expressly reserved by Seagate Technology, LLC.
 * 
 * Author: Yogesh Lahane <yogesh.lahane@seagate.com>
 *
 */
 
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <assert.h>
#include <fault.h>
#include <fault-points.h>

/**
 * ##############################################################
 * # 		Fault Point ID Definations.			#
 * ##############################################################
 */

static int fp_id_equal(fault_id_t *fp_id1, fault_id_t *fp_id2)
{
	return (!strcmp(fp_id1->fpi_func, fp_id2->fpi_func)) &&
		(!strcmp(fp_id1->fpi_tag, fp_id2->fpi_tag));
}

/**
 * ##############################################################
 * # 		Fault Point Data Definations.			#
 * ##############################################################
 */

void fp_data_init(fault_data_t *fp_data, fault_type_t fp_type,
		fault_spec_t fp_spec)
{
	fp_data->fpd_type = fp_type;
	fp_data->fpd_hit_count = 0;
	fp_data->fpd_hit_once = 0;
	fp_data->fpd_spec = fp_spec;
}

void fp_data_inc_hitcount(fault_data_t *fp_data)
{
	fp_data->fpd_hit_count++;
}

/**
 * ##############################################################
 * # 		Fault Point Spec handler Definations.		#
 * ##############################################################
 */

static inline int fp_once_spec(fault_data_t *fp_data)
{
	int rc = 0;

	if (fp_data->fpd_hit_count >= fp_data->fpd_spec.n_and_m.hit_start &&
		fp_data->fpd_hit_once == 0) {
		fp_data->fpd_hit_once = 1;
		rc = 1;
	}

	return rc;
}

static inline int fp_always_spec(fault_data_t *fp_data)
{
	return (fp_data->fpd_hit_count >= fp_data->fpd_spec.n_and_m.hit_start);
}

static inline int fp_repeat_spec(fault_data_t *fp_data)
{
	return (fp_data->fpd_hit_count >= fp_data->fpd_spec.n_and_m.hit_start &&
		fp_data->fpd_hit_count <= fp_data->fpd_spec.n_and_m.hit_end);
}

static inline int fp_skip_spec(fault_data_t *fp_data)
{
	return ((fp_data->fpd_hit_count >= fp_data->fpd_spec.n_and_m.hit_start &&
		fp_data->fpd_hit_count <= fp_data->fpd_spec.n_and_m.hit_end))
			? 0 : 1;
}

static inline int fp_delay_spec(fault_data_t *fp_data)
{
	sleep(fp_data->fpd_spec.delay);
	return 1;
}

static inline int fp_random_spec(fault_data_t *fp_data)
{
	return (fp_data->fpd_spec.prob >= (random() % FI_RAND_PROB_SCALE));
}

static inline int fp_user_func_spec(fault_data_t *fp_data)
{
	return fp_data->fpd_spec.user.func_cb(fp_data->fpd_spec.user.func_cb_data);
}

static fps_handler_t fault_spec_table[FP_TYPE_NR] = {
	[FP_TYPE_ONCE]		= fp_once_spec,
	[FP_TYPE_ALWAYS]	= fp_always_spec,
	[FP_TYPE_REPEAT]	= fp_repeat_spec,
	[FP_TYPE_SKIP]		= fp_skip_spec,
	[FP_TYPE_DELAY]		= fp_delay_spec,
	[FP_TYPE_RANDOM]	= fp_random_spec,
	[FP_TYPE_USER_FUNC]	= fp_user_func_spec,
};

_PRIVATE inline fps_handler_t fp_spec_get_handler(fault_type_t fp_type)
{
	return fault_spec_table[fp_type];
}

fault_table_t *fault_table = NULL;

/**
 * ##############################################################
 * # 		Fault Point Table Handler Definations.		#
 * ##############################################################
 */

void fp_table_init(void)
{
	int rc = 0;
	uint32_t fpt_size = 0;

	fault_table = malloc(sizeof(fault_table_t));
	assert(fault_table != NULL);

	// Assign initial fault_table size.
	// Table will go dynamically as and when new faults
	// get introduced.
	fault_table->fpt_size = IFAULT_INIT_TABLE_SIZE;
	fpt_size = fault_table->fpt_size;

	fault_table->fpt_list = malloc(fpt_size * sizeof(fault_state_t));
	assert(fault_table->fpt_list != NULL);

	fault_table->fpt_idx = 0;
	
	// Init table lock.
	rc = pthread_mutex_init(&fault_table->fpt_lock, NULL);
	assert(rc == 0);
}

void fp_table_cleanup(void)
{
	int i = 0;
	fault_state_t *fp_state = NULL;

	pthread_mutex_lock(&fault_table->fpt_lock);

		for (i = 0; i < fault_table->fpt_idx; i++) {
			fp_state = &fault_table->fpt_list[i];
			fp_state_free_id(fp_state);
			// Destory the lock.
			pthread_mutex_destroy(&fp_state->fps_lock);
		}

	pthread_mutex_unlock(&fault_table->fpt_lock);

	// Destory the lock.
	pthread_mutex_destroy(&fault_table->fpt_lock);

	// Free the states_list.
	free(fault_table->fpt_list);
	fault_table->fpt_list = NULL;

	// Free the table.
	free(fault_table);
	fault_table = NULL;
}

static void fp_table_realloc_states(void)
{
	uint32_t new_size = 0;
	fault_state_t *state_list = NULL;
	
	state_list = fault_table->fpt_list;
	fault_table->fpt_size *= 2;
	new_size = fault_table->fpt_size;

	state_list = realloc(state_list, new_size * sizeof (fault_state_t));
	assert(state_list != NULL);
}
/**
 * ##############################################################
 * # 		Fault Point State Handler Definations.		#
 * ##############################################################
 */

static void fp_state_set_id(fault_state_t *fp_state, fault_id_t *fp_id)
{
	assert(fp_state != NULL);
	assert(fp_id != NULL);

	fp_state->fps_id.fpi_func = strdup(fp_id->fpi_func);
	assert(fp_state->fps_id.fpi_func != NULL);

	fp_state->fps_id.fpi_tag = strdup(fp_id->fpi_tag);
	assert(fp_state->fps_id.fpi_tag != NULL);
}

_PRIVATE void fp_state_free_id(fault_state_t *fp_state)
{
	fault_id_t *fp_id;

	assert(fp_state != NULL);

	fp_id = &fp_state->fps_id;

	free((void*)fp_id->fpi_func);
	free((void*)fp_id->fpi_tag);
}

static void fp_state_init(fault_state_t *fp_state, fault_id_t *fp_id)
{
	int rc = 0;

	assert(fp_state != NULL);
	assert(fp_id != NULL);

	rc = pthread_mutex_init(&fp_state->fps_lock, NULL);
	assert(rc == 0);

	fp_state->fps_enabled = 0;
	fp_state->fps_fp = NULL;

	fp_state_set_id(fp_state, fp_id);
}

_PRIVATE void fp_state_find(fault_id_t *fp_id, fault_state_t **ret_fp_state)
{
	int i = 0;
	int found = 0;
	fault_state_t *fp_state = NULL;

	assert(fp_id != NULL);

	pthread_mutex_lock(&fault_table->fpt_lock);

		for (i = 0; i < fault_table->fpt_idx; i++) {
			fp_state = &fault_table->fpt_list[i];
			if (fp_id_equal(&fp_state->fps_id, fp_id)) {
				found = 1;
				*ret_fp_state = fp_state;
				break;
			}
		}

		if (!found) {
			// Try to allocate new state.
			if (fault_table->fpt_idx == fault_table->fpt_size) {
				// Realloc fpt_list
				fp_table_realloc_states();
			}

			fp_state = &fault_table->fpt_list[fault_table->fpt_idx];
			fault_table->fpt_idx++;

			// Init state
			fp_state_init(fp_state, fp_id);

			*ret_fp_state = fp_state;
		}

	pthread_mutex_unlock(&fault_table->fpt_lock);
}

int fp_state_enable(fault_state_t *fp_state)
{
	int rc = 0;
	
	assert(fp_state != NULL);
 
	pthread_mutex_lock(&fp_state->fps_lock);

		if (fp_state->fps_enabled == 1)
			rc = 1;
		fp_state->fps_enabled = 1;

	pthread_mutex_unlock(&fp_state->fps_lock);

	return rc;
}

int fp_state_disable(fault_state_t *fp_state)
{
	int rc = 0;

	assert(fp_state != NULL);

	pthread_mutex_lock(&fp_state->fps_lock);

		if (fp_state->fps_enabled == 0)
			rc = 1;
		fp_state->fps_enabled = 0;

	pthread_mutex_unlock(&fp_state->fps_lock);

	return rc;
}
