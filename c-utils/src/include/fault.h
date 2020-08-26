/*
 * Filename: fault.h
 * Description: Headers for fault framework.
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

#ifndef _IFAULT_H
#define _IFAULT_H

#include <stdint.h>
#include <pthread.h> /* mutexes */
#include <assert.h>
#include <common.h>

/**
 * Represents the fault point set.
 * It provides interfaces to update the fault points and also check if a
 * Particular fault point is active or not.
 */

/* Fault Point Types */
typedef enum fault_type {
	/* Triggers only on first hit, then becomes disabled automatically */
	FP_TYPE_ONCE,
	/* Always triggers when enabled */
	FP_TYPE_ALWAYS,
	/**
	 * Doesn't trigger first N times, then triggers next M times, then
	 * repeats this cycle
	 */
	FP_TYPE_REPEAT,
	FP_TYPE_SKIP,
	/* Sleeps for specified amount of time */
	FP_TYPE_DELAY,
	 /* Triggers with a given probability */
	FP_TYPE_RANDOM,
	/* User defined call back fuction */
	FP_TYPE_USER_FUNC,
	/* Number of fault points */
	FP_TYPE_NR,

} fault_type_t;

/**
 * User func call back.
 */
typedef int (*func_cb_t)(void *);

typedef union fault_spec {
	struct {
		/* Point when FP should be triggered */
		uint32_t hit_start;
		/* Point beyond which FP should not be triggered */
		uint32_t hit_end;
	} n_and_m;

	struct {
		/* User func call back */
		func_cb_t func_cb;
		void *func_cb_data;
	} user;

	/* Delay amount FP should add */
	uint32_t delay;
	/**
	 * Probability with which FP is triggered (for M0_FI_RANDOM
	 * type), it's an integer number in range [1..100], which means
	 * a probability in percents, with which FP should be triggered
	 * on each hit
	 */
	uint32_t prob;

} __attribute__((packed)) fault_spec_t;

/**
 * Fault point spec's.
 */
#define FP_ONCE(h_point)							\
	FP_TYPE_ONCE,								\
	((const fault_spec_t)							\
		{								\
			.n_and_m.hit_start 	= (h_point)			\
		}								\
	)
					

#define FP_ALWAYS()								\
	FP_TYPE_ALWAYS,								\
	((const fault_spec_t)							\
		{								\
			.n_and_m.hit_start 	= (1L)				\
		}								\
	)
					
#define FP_REPEAT(h_start, h_end)						\
	FP_TYPE_REPEAT,								\
	((const fault_spec_t)							\
		{								\
			.n_and_m.hit_start 	= (h_start),			\
			.n_and_m.hit_end 	= (h_end)			\
		}								\
	)
					
#define FP_SKIP(h_start, h_end)							\
	FP_TYPE_SKIP,								\
	((const fault_spec_t)							\
		{								\
			.n_and_m.hit_start 	= (h_start),			\
			.n_and_m.hit_end	= (h_end)			\
		}								\
	)
					
#define FP_DELAY(time)								\
	FP_TYPE_DELAY,								\
	((const fault_spec_t)							\
		{								\
			.delay			= (time)			\
		}								\
	)

#define FP_RANDOM(probability)							\
	FP_TYPE_RANDOM,								\
	((const fault_spec_t)							\
		{								\
			.prob			= (probability)			\
		}								\
	)

#define FP_USER_FUNC(function_cb, function_cb_data)				\
	FP_TYPE_USER_FUNC,							\
	((const fault_spec_t)							\
		{								\
			.user.func_cb		= (function_cb),		\
			.user.func_cb_data	= (function_cb_data)		\
		}								\
	)
					
typedef struct fault_state fault_state_t;
typedef struct fault_data fault_data_t;
typedef struct fault_table fault_table_t;

/**
 * Holds information about "fault point" (FP).
 */
typedef struct fault {
	/* Subsystem/module name */
	const char	*fp_module;
	/* File name */
	const char	*fp_file;
	/* Line number */
	uint32_t	fp_line_num;
	/* Function name */
	const char	*fp_func;
	/**
	 * Tag - one or several words, separated by underscores, aimed to
	 * describe a purpose of the fault point and uniquely identify this FP
	 * within a current function
	 */
	const char	*fp_tag;
	/* Fault point state */
	fault_state_t	*fp_state;

} __attribute__((packed)) fault_t;

/* Fault Point ID */
typedef struct fault_id {
	/* Fault point function name where fault is defined */
	const char *fpi_func;
	/* Unique Tag that identifies fault point in the function */
	const char *fpi_tag;

} __attribute__((packed)) fault_id_t;

/**
 * Fault Framework Interfaces
 * Note: These interfaces are not thread safe
 */
_PUBLIC void fault_init(void);
_PUBLIC void fault_cleanup(void);

_PUBLIC int fault_enabled(fault_id_t *fp_id);
_PUBLIC void fault_enable(fault_id_t *fp_id);
_PUBLIC void fault_disable(fault_id_t *fp_id);
_PUBLIC void fault_register(fault_t *fp, fault_type_t fp_type,
		fault_spec_t fp_spec);
_PUBLIC void fault_print(fault_id_t *fp_id);

#ifdef FAULT_INJECT

#define IFAULT_INIT_TABLE_SIZE	256

/**
 * Defines a fault point and checks if it's enabled.
 *
 * FP registration occurs only once, during first time when this macro is
 * "executed". fault_register() is used to register FP in a global dynamic list,
 * which may introduce some delay if this list already contains large amount of
 * registered fault points.
 *
 * A typical use case for this macro is:
 *
 * @code
 *
 * void *nsal_alloc(size_t n)
 * {
 *	...
 *	if (FP_ENABLED("pretend_failure", FP_ALWAYS()))
 *		return NULL;
 *	...
 * }
 *
 * @endcode
 *
 * It creates a fault point with tag "pretend_failure" in function "nsal_alloc",
 * which can be enabled/disabled from external code with something like the
 * following:
 *
 * @code
 *
 * 	fault_id_t fp_id;
 *
 * 	fp_id.fpi_func = "nsal_alloc";
 * 	fp_id.fpi_tag = "pretend_failure";
 *
 *	fault_enable(&fp_id);
 *
 * @endcode
 *
 * @param tag short descriptive name of fault point, usually separated by
 *            and uniquely identifies this FP within a current
 *            function
 *
 * @return    true, if FP is enabled
 * @return    false otherwise
 */

#define FP_ENABLED(tag, spec)				\
({							\
	static fault_t fp = {				\
		.fp_state    = NULL,			\
 /* TODO: add some macro to automatically get name of current module */ \
		.fp_module   = "UNKNOWN",		\
		.fp_file     = __FILE__,		\
		.fp_line_num = __LINE__,		\
		.fp_func     = __func__,		\
		.fp_tag      = (tag),			\
	};						\
							\
	if (likely(fp.fp_state == NULL)) {		\
		fault_register(&fp, spec);		\
		assert(fp.fp_state != NULL);		\
	}						\
							\
	fault_id_t fp_id =				\
		{					\
			.fpi_func = __func__,		\
			.fpi_tag  = (tag)		\
		};					\
							\
	fault_enabled(&fp_id);				\
})

#else

#define IFAULT_INIT_TABLE_SIZE		(1L)

#define FP_ENABLED(tag, spec)		(0L)

#endif /* FAULT_INJECT */

#endif /* _IFAULT_H */

