/**
 * Filename: fault-internal.h
 * Description: Internal Headers for fault framework.
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

#ifndef _IFAULT_INTERNAL_H
#define _IFAULT_INTERNAL_H

#include <string.h>
#include <stdarg.h>
#include <common.h>

#define FI_RAND_PROB_SCALE	100

/**
 * Fault point data.
 */
typedef struct fault_data {
	/* Fault point type */
	fault_type_t	fpd_type;
	/* Number of times FP was checked */
	uint32_t	fpd_hit_count;
	/* Fault hit once */
	int 		fpd_hit_once;
	/* Fault Point spec */ 
	fault_spec_t	fpd_spec;

} __attribute__((packed)) fault_data_t;

/**
 * Faunt point spec handler
 */
typedef int (*fps_handler_t)(fault_data_t *fp_data);

/**
 * Reference to the "state" structure, which holds information about
 * current state of fault point (e.g. enabled/disabled, triggering
 * algorithm, FP data, etc.)
 */
typedef struct fault_state {
	/* Lock */
	pthread_mutex_t	fps_lock;
	/* Is fault point enabled? */
	int		fps_enabled;
	/* Fault point ID */
	fault_id_t	fps_id;
	/* Fault point data*/
	fault_data_t	fps_data;
	/* Fault point state handler func */
	fps_handler_t	fps_handler;
	/* Fault point info */
	fault_t		*fps_fp;

} __attribute__((packed)) fault_state_t;

/**
 * Fault point table
 */
typedef struct fault_table {
	/* Lock */
	pthread_mutex_t	fpt_lock;
	/* Max fp_list allocation size */
	uint32_t	fpt_size;
	/* Next available slot in fp_list */
	uint32_t	fpt_idx;
	/* list of poiters to fault points */
	fault_state_t	*fpt_list;

} __attribute__((packed)) fault_table_t;

/**
 * fault_table is defined in fault-points.c
 */
_PRIVATE extern fault_table_t *fault_table;

_PRIVATE void fp_table_init(void);
_PRIVATE void fp_table_cleanup(void);
_PRIVATE void fp_state_find(fault_id_t *fp_id, fault_state_t **fp_state);
_PRIVATE int fp_state_enable(fault_state_t *fp_state);
_PRIVATE int fp_state_disable(fault_state_t *fp_state);
_PRIVATE void fp_state_free_id(fault_state_t *fp_state);
_PRIVATE fps_handler_t fp_spec_get_handler(fault_type_t fp_type);
_PRIVATE void fp_data_inc_hitcount(fault_data_t *fp_data);
_PRIVATE void fp_data_init(fault_data_t *fp_data, fault_type_t fp_type,
		fault_spec_t fp_spec);

#endif
