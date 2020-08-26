/*
 * Filename:	tsdb.h
 * Description:	This module defines TSDB interfaces.
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

#ifndef TSDB_H_
#define TSDB_H_
/******************************************************************************/
#include <stdbool.h> /* bool type */
#include <stdint.h> /* SintN_t types */

/******************************************************************************/
/* TSDB
 * ----
 *  TSDB is an abstraction layer over a time series database.
 *  At this moment it supports only one engine - ADDB.
 *  The main function (macro, actually) is TSDB_ADD. It adds a record
 *  into the database. Records are added in a way that it has almost
 *  zero impact on performance. After successful program execution,
 *  the corresponding file (for example, an ADDB stob) can be used
 *  for further analysis.
 *
 *  Non-implemented functionality:
 *	- Decoder. TSDB records contain only numbers. These numbers
 *	can be mapped to human-readable strings.
 *	- Push/Pop. ADDB supports changing of the current context,
 *	however right now is optional.
 *
 *
 * Enabling/Disabling TSDB
 * -----------------------
 *
 *  There are 3 ways to enable/disable parts of TSDB:
 *	- Compile-time switch (ENABLE_TSDB_{X}).
 *	- Initial state of the engine.
 *	- Run-time switch.
 *  Imagine, there is a house and there is a power generator in that house
 *  that works on gas or a similar substance. This generator automatically
 *  starts working once you put some gas into it, and it cannot be turned
 *  off afterwards. There is also some wires that connect the generator
 *  with an onoff (run-time) switch that turns on/off a lamp in that house.
 *  Using this example, these ways can be described as following:
 *	- Compile-time switch - whether you want to install wires in the
 *	house or not. If there are no wires then nothing will work.
 *	- Initial state of the engine. Once you turn the power generator on,
 *	you cannot turn it off later. It will continue using the resources.
 *	In the same way, the TSDB engine cannot be disabled.
 *	- Run-time switch - it is just like a switch in the room
 *	that turns on/off the lamp. If you turn it off then you can save
 *	some resources.
 * Use-cases:
 *	* Compile-time switch allows us to completely turn off tracing.
 *	  For example, if we want to compile the project without M0.
 *	* Initial state of the engine allows us to do almost the same thing
 *	  as the previous one but at the startup time without recompiling
 *	  the program.
 *	* Run-time switch allows us to disable tracing dynamically
 *	  when the program already runs. It can be used when we need to
 *	  perform measurements only at specific points of timescale.
 */

/******************************************************************************/
/* Internal TSDB API. Each TSDB engine shall implement this set of
 * declarations.
 */

/** Add a record into the db.
 * @param id Action ID.
 * @param n Number of values.
 * @param value Array of values.
 *
 * The db is a mapping between Action IDs and values.
 * So that, K=id and V=(n,value).
 * The keys form a multiset -- it is allowed to have different values
 * with the same keys. In other words, the reverse mapping (V -> K) is
 * surjective.
 * The Action ID is needed only to draw the lines between different
 * modules and operations.
 */
static inline void tsdb_add(uint64_t id, int n, const uint64_t *value);

/** Tell the engine to leave the current thread.
 * This call is needed only for ADDB and only for specific cases where
 * we want to "detach" ADDB from the thread.
 * Any other implementation of the internal TSDB API can define it
 * as no-op.
 */
static inline void tsdb_leave(void);

/******************************************************************************/
/* Import a TSDB engine based on compile-time flags */
#if defined(ENABLE_TSDB_ADDB)
#include "perf/tsdb-addb.h"
#elif defined(ENABLE_TSDB_PRINTF)
#include "perf/tsdb-printf.h"
#else
/* Use stubs instead of the actual ADDB API
 * when ADDB-based is disabled at compile-time.
 */
#include "perf/tsdb-dummy.h"
#endif

/******************************************************************************/
/** Expression-like trace point.
 * @param __rv Return value of the macro.
 * @param __action_id Action ID - the mandatory part of any record.
 * @return __rv The value is returned as it is.
 *
 * The __rv parameter (and the corresponding GCC extension enabled by default)
 * allows using this macro as expression but not just as statement.
 * Here is the common use case:
 *
 * @{code}
 * void foo(int a) {
 *	int b = 1;
 *	int rc = 0;
 *
 *	// Puts (FOO_ENTER_ID, a) into the db.
 *	TSDB_ADD_EX(NULL, FOO_ENTER_ID, a);
 *
 *	// some logic here to change the rc
 *	rc = (b == a) ? 0 : -EINVAL;
 *
 *	// Returns rc and puts (FOO_EXIT_ID, a, b, rc) tuple into the db.
 *	return TSDB_ADD_EX(FOO_EXIT_ID, rc, a, b, rc);
 * }
 * @{endcode}
 *
 */
#define TSDB_ADD_EX(__rv, __action_id, ...)				\
({									\
	if (tsdb_is_on()) {						\
		const uint64_t __args[] = { __VA_ARGS__ };		\
		int __n_args  = sizeof(__args) / sizeof(__args[0]);	\
		tsdb_add(__action_id, __n_args, __args);		\
	}								\
	 __rv;								\
})

/** Statement-like trace point. */
#define TSDB_ADD(...) TSDB_ADD_EX(NULL, __VA_ARGS__)

/** Detaches the current thread from the TSDB engine. */
#define TSDB_LEAVE() tsdb_leave()

/******************************************************************************/
/** Check if TSDB is enabled.
 * @see tsdb_set_onoff_state for details.
 */
bool tsdb_is_on(void);

/** Check if TSDB engine was started in tsdb_init() call.
 * This function may be used at initialization state of the underlying
 * TSDB backend.
 */
bool tsdb_is_engine_on(void);

/** Enable or disable TSDB at runtime.
 * NOTE1: It only disables the process of generating new entires;
 *  see TSDB_ADD_EX macro and tsdb_is_on() function for details.
 *  Any existing entires will be dumped eventually. Also, the engine
 *  cannot be turned off by this call. It can be done using ENABLE_TSDB_{X}
 *  macro at compile-time.
 * NOTE2: When TSDB engine is disabled at compile time, this function is noop.
 *  It does nothing except changing one local variable.
 */
void tsdb_set_rt_state(bool rt_state);

/** Initialize TSDB.
 * See the "Enabling/Disabling TSDB" section for the details.
 * @param engine_state Set "true" if TSDB engine should be available.
 *		       Note: this value cannot be changed later.
 * @param rt_stat Set if "true" if TSDB should be enabled at runtime.
 *		  ::tsdb_set_rt_state can be used to change it.
 * @return -errno if tsdb cannot be initialized; 0 otherwise.
 */
int tsdb_init(bool engine_state, bool rt_state);

/** Finalizes TSDB. */
void tsdb_fini(void);

/******************************************************************************/
#endif /* TSDB_H_ */
