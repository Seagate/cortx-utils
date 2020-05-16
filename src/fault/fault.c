/**
 * Filename: fault.c
 * Description: Fault injection Framework.
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

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <unistd.h>
#include <fault.h>
#include <internal/fault-points.h>

/**
 * fault_init:
 * Initializes Fault Framework
 */
_PUBLIC void fault_init(void)
{
	unsigned int random_seed;

	fp_table_init();

	// Initialize pseudo random generator, which is used in FI_TYPE_RANDOM
 	// triggering algorithm.
	random_seed = getpid() ^ time(NULL);
	srandom(random_seed);
}

/**
 * fault_cleanup:
 * Initializes Fault Framework
 */
_PUBLIC void fault_cleanup(void)
{
	fp_table_cleanup();
}

/**
 * fault_register:
 * Register the fault point.
 */
_PUBLIC void fault_register(fault_t *fp, fault_type_t fp_type,
		fault_spec_t fp_spec)
{
	fault_id_t fp_id;
	fault_state_t *fp_state = NULL;

	// Construct Fault Point ID.
	fp_id.fpi_func = fp->fp_func;
	fp_id.fpi_tag = fp->fp_tag;

	// Find the Fault Point State.
	fp_state_find(&fp_id, &fp_state);
	assert(fp_state != NULL);

	// Check for duplicate fault point registration.
	assert(fp_state->fps_fp == NULL);

	pthread_mutex_lock(&fp_state->fps_lock);

		// Attach fault point data.
		fp_data_init(&fp_state->fps_data, fp_type, fp_spec);

		// Attach spec handler func.
		fp_state->fps_handler = fp_spec_get_handler(fp_type);

		// Attach fault point to the state.
		fp_state->fps_fp = fp;

		// Attach the state to the fault point.
		fp->fp_state = fp_state;

	pthread_mutex_unlock(&fp_state->fps_lock);
}

/**
 * fault_enabled:
 * Check fault point is enabled or not.
 */

_PUBLIC int fault_enabled(fault_id_t *fp_id)
{
	int rc = 0;
	fault_state_t *fp_state = NULL;
	fault_data_t *fp_data = NULL;

	fp_state_find(fp_id, &fp_state);
	assert(fp_state != NULL);

	fp_data = &fp_state->fps_data;

	pthread_mutex_lock(&fp_state->fps_lock);

		// Increment the hit_count.
		fp_data_inc_hitcount(fp_data);

		// Check fault point is active? 	
		if (fp_state->fps_enabled) {
			rc = fp_state->fps_handler(fp_data);
		}

	pthread_mutex_unlock(&fp_state->fps_lock);

	return rc;
}

/**
 * fault_enable:
 * Enable the fault point.
 */
_PUBLIC void fault_enable(fault_id_t *fp_id)
{
	fault_state_t *fp_state = NULL;

	fp_state_find(fp_id, &fp_state);
	assert(fp_state != NULL);

	fp_state_enable(fp_state);
}

/**
 * fault_enable:
 * Disable the fault point.
 */
_PUBLIC void fault_disable(fault_id_t *fp_id)
{
	fault_state_t *fp_state = NULL;

	fp_state_find(fp_id, &fp_state);
	assert(fp_state != NULL);

	fp_state_disable(fp_state);

}
