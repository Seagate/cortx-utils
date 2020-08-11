/**
 * Filename:	operation.h
 * Description:	This module defines Operation API.
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
 * please email opensource@seagate.com or cortx-questions@seagate.com.*
 */
#ifndef OPERATION_H_
#define OPERATION_H_
/******************************************************************************/
#include <stdint.h> /* uintX_t */
#include <inttypes.h> /* PRIxY */
#include "perf/perf-counters.h" /* import all perf counters definitions */

/* Operation API overview
 * ----------------------
 *
 * Operation API provides its users with an ability to establish
 * manual tracing of function calls.
 * There are a plenty of existing tools and libraries that
 * provide similar functionality for automatic tracing
 * (valgrind callgraph tool, linux perf etc.) and manual tracing
 * (various trace-point libraries).
 *
 * Operation API has the notion of opcall (or just call) that
 * describes one particular call to a function. These calls can be grouped
 * together into opstack.
 *
 * Since we want to be able to identify the function that was called
 * within an opcall, we need an ID for that function.
 * This ID has to be a value that is constant, and does not depend
 * on linking or compiling processes (otherwise, we could use the trick with
 * a reference variable). Because of that this ID has to be defined
 * in the source code, and it has to be unique.
 * That's where we introduce operation tags. They help us to identify functions,
 * and the modctx.mod_id designators help us to keep operation tags unique
 * only within one single module.
 *
 * opcall.fn_id is the field where an operation tag is stored.
 * The field is not called "optag" just for the sake of clarity of the scope:
 *	op.mod - Module
 *	op.fn_id - Function in the module
 *	op.call_id - One of the calls to the function.
 * So basically, fn_id is an alias for operation tag.
 *
 * Operation tag and module creates the (fn_id, mod_id) tuple. This tuple
 * is called "action" or "action ID" in TSDB. An action is unique across
 * the whole system.
 * The relation between fn_id, mod_id and action can be described in
 * the following way:
 *
 * @{code}
 *	// A global enum that can be used by any module defined in the list.
 *	enum ::m { MOD_A, MOD_B, MOD_C, ... }
 *	// Operation tags for the module MOD_A (and defined there).
 *	enum mod_a::optags { OP_1, OP_2, ... };
 *	// Operation tags for the module MOD_B (and defined there).
 *	enum mod_b::optags { OP_1, OP_2, ... };
 *
 *	constant ::MOD_OFFSET;
 *
 *	mod_a {
 *		import ::m;
 *		op_1() {
 *			action = (::m::MOD_A << ::MOD_OFFSET) | mod_a::OP_1;
 *		}
 *		...
 *	}
 *	mod_b {
 *		import ::m;
 *		op_1() {
 *			action = (::m::MOD_B << ::MOD_OFFSET) | mod_b::OP_1;
 *		}
 *	}
 * @{endcode}
 *
 */

/******************************************************************************/
/* Public data types */

/** Per-module context that helps to maintain per-module operation tags.
 * See the overview for the details about relations between modules
 * and operation tags.
 */
struct modctx {
	/** Generates unique IDs for each call within the module. */
	uint64_t op_counter;
	/** Unique (across the system) ID for the module. */
	uint64_t mod_id;
};

/** Module context initializer. */
#define MODCTX_INIT(__mod_id) (struct modctx) { \
	.op_counter = 0,			\
	.mod_id = __mod_id,			\
}

/** The structure defines one single call in a callstack */
struct opcall {
	/** Unique identifier (generated) of the call. */
	uint64_t call_id;
	/** Unique identifier (hardcoded) of the function
	 * that was used within the call.
	 */
	uint64_t fn_id;
	/** Reference to the module where the function
	 * was called.
	 */
	const struct modctx *mod;
	/** Function name of the point where "opcall" was created.
	 * It is not required for tracing events (fn_id is used
	 * instead); however, it is required for debugging.
	 */
	const char *fn_name;
};

/** Format string for debugging representation of "opcall" */
#define OPCALL_DBG_FMT "c=%" PRIu64 ", f=%" PRIu64 ", m=%" PRIu64 ", n='%s'"

/** Format arguments for OPCALL_DBG_FMT. */
#define OPCALL_DBG_P(_opc)	\
	(_opc)->call_id,	\
	(_opc)->fn_id,		\
	(_opc)->mod->mod_id,	\
	(_opc)->fn_name


enum {
	/** The maximum count of elements in a stack
	 * of operation calls.
	 * At this moment, 8 is a relatively safe value, so
	 * we double it, and use it here.
	 * NOTE: The size and the whole structure may be a subject
	 * to performance optimizations when we encounter
	 * such a need. But right now we just maintain a safe boundary.
	 */
	MAX_OPSTACK_DEPTH = 16,
};
_Static_assert(MAX_OPSTACK_DEPTH > 0, "opstack cannot be empty");

/** An object that keeps the information about stack of calls.
 * It is an "Ariadne's thread" between the place where operation
 * was originated (described by "head", i.e. ctxstack[0] value)
 * and any location to which the opstack was propogated.
 */
struct opstack {
	/** Call stack information. */
	struct opcall ctxstack[MAX_OPSTACK_DEPTH];
	/** The current stack size. */
	uint64_t depth;
};

/******************************************************************************/
/* Private intefaces: opcall and opstack helpers */

/** Initializes a new instance of a call to a function (or operation)
 * within a module.
 * Note:
 *  This macro uses a builtin function to ensure atomicity of the counter.
 *  Since the compiler and processor are able to re-order operations and
 *  access to memory, we have to use a primitive that helps to perform
 *  atomic increment. At this moment we are using gcc-4.8, and C11 is not
 *  specified as the standard, so we have to use the "old" __sync builtins.
 *  Once the gcc version and/or the standard version are upgraded, we can
 *  switch to the __atomic builtins or the atomic_ data types.
 */
#define OPCALL_INIT(__mod, __tag) (struct opcall) {			\
	.call_id = __sync_add_and_fetch(&(__mod)->op_counter, 1),	\
	.mod = (__mod),							\
	.fn_id = (__tag),						\
	.fn_name = __FUNCTION__,					\
}

#define OPCALL_INIT_EMPTY() (struct opcall) {	\
	.call_id = 0,				\
}

/** Get the origin of an operation. */
static inline struct opcall *opstack_head(struct opstack *opstack)
{
	return &opstack->ctxstack[0];
}

/** Get the current context of an operation. */
static inline struct opcall *opstack_curr(struct opstack *opstack)
{
	return &opstack->ctxstack[opstack->depth - 1];
}

/** Get the caller of the current operation. */
static inline struct opcall *opstack_caller(struct opstack *opstack)
{
	return &opstack->ctxstack[opstack->depth - 2];
}

/** Initializes an opstack structure with the very first value (origin). */
#define OPSTACK_INIT(__mod, __tag) (struct opstack) {		\
	.ctxstack[0] = OPCALL_INIT(__mod, __tag),		\
	.depth = 1,						\
}

/** Initializes an opstack structure with no data.
 * Any opstack created by this call is considered invalid until
 * OPSTACK_INIT is called to populate it again. It is because the following
 * invariant should be held for a valid opstack:
 *	opstack.depth > 0
 * It means a valid opstack always has the origin (head).
 * This macro can be used to "finalize" an opstack structure.
 */
#define OPSTACK_INIT_EMPTY() (struct opstack) {			\
	.ctxstack[0] = OPCALL_INIT_EMPTY(),			\
	.depth = 0,						\
}

/******************************************************************************/
/* Public interface: op and ctx mgmt. */

/** Origin of an operation.
 * This macro should be put at the location where we want to start
 * tracking an operation.
 * Example:
 * @{code}
 *	struct opstack;
 *	opstack_begin(&opstack, &g_my_mod, MY_TAG, some_arg);
 *	other_args = arg_to_other_arg(some_arg);
 *	rc = do_smth(&opstack, other_args);
 *	opstack_end(&opstack, rc);
 *	return rc;
 * @{endcode}
 *
 * @param _op Uninitialized opstack object.
 * @param _mod Pointer to the module context.
 * @param _tag ID of function/operation.
 * @param __VA_ARGS__ Any uint64_t values.
 */
#define opstack_begin(_op, _mod, _tag, ...) do {			\
	*(_op) = OPSTACK_INIT(_mod, _tag);				\
	PERFC_OP_EE(							\
		opstack_curr(_op)->mod->mod_id,				\
		opstack_curr(_op)->fn_id,				\
		opstack_curr(_op)->call_id,				\
		PERFC_EE_OP_BEGIN,					\
		__VA_ARGS__						\
	);								\
} while(0)

/** Defines the point where an operation ends.
 * @param _op Initialized opstack object.
 * @param __VA_ARGS__ Any uint64_t values.
 */
#define opstack_end(_op, ...) do { \
	PERFC_OP_EE(							\
		opstack_curr(_op)->mod->mod_id,				\
		opstack_curr(_op)->fn_id,				\
		opstack_curr(_op)->call_id,				\
		PERFC_EE_OP_END,					\
		__VA_ARGS__						\
	);								\
	*(_op) = OPSTACK_INIT_EMPTY();					\
} while(0)

/** Defines the point where an operation ends (as an expression).
 * The same as opstack_end but expression. Example of usage:
 * {code}
 *	opstack op;
 *	opstack_begin(&op, &m, MY_TAG);
 *	// ...
 * out:
 *	return opstack_end_rc(&op, rc);
 * {endcode}
 */
#define opstack_end_rc(_op, __rc, ...) ({				\
	PERFC_OP_EE(							\
		opstack_curr(_op)->mod->mod_id,				\
		opstack_curr(_op)->fn_id,				\
		opstack_curr(_op)->call_id,				\
		PERFC_EE_OP_END,					\
		__rc,							\
		__VA_ARGS__						\
	);								\
	*(_op) = OPSTACK_INIT_EMPTY();					\
	__rc;								\
})

/** Change the context. */
#define opstack_push(__op, __mod, __tag) do {		\
	if ((__op)->depth < MAX_OPSTACK_DEPTH) {	\
		(__op)->ctxstack[(__op)->depth++] =	\
			OPCALL_INIT(__mod, __tag);	\
	}						\
} while (0)

/** Restore the context. */
#define opstack_pop(__op) do {				\
	if ((__op)->depth > 0) {			\
	(__op)->ctxstack[(__op)->depth--] =		\
		OPCALL_INIT_EMPTY();			\
	}						\
} while (0)

/** Mark the point of connection between an operation
 * and an external operation.
 */
#define opstack_map_head2external(__op, __map_tag, __key, ...) do {	\
	PERFC_MAP(opstack_head(__op)->mod->mod_id,			\
		  opstack_head(__op)->fn_id,				\
		  opstack_head(__op)->call_id,				\
		  __map_tag, __key, __VA_ARGS__);			\
} while (0);

/******************************************************************************/
/* Public interface: hardcoded list of modules. */

/** A hardcoded list of modules to be used within operation tags.
 * The list is hardcoded due to the following reasons:
 *	- Decoding of records should be independent from ordering
 *	of loaded modules. Otherwise, we could use reference variables or
 *	something similar. However, it has been proven that such approach
 *	leads to significant troubles during decoding stage.
 *	- There has to be no collisions in the list. Again, there may be
 *	a lot of ways to ensure there are no collisions, but this is
 *	the simplest one.
 */
enum tsdb_modules {
	/* A list of well-known modules */
	TSDB_MOD_UTILS = 0,
	TSDB_MOD_DSAL,
	TSDB_MOD_NSAL,
	TSDB_MOD_FS,
	TSDB_MOD_FSUSER,
	TSDB_MOD_UT,
	TSDB_MOD_LAST = TSDB_MOD_UT,

	/* Custom module ids. Note: this range
	 * of ids is not protected from collisions
	 */
	TSDB_MOD_CUSTOM_START = TSDB_MOD_LAST + 1,
	TSDB_MOD_CUSTOM_END = TSDB_MOD_LAST + 16,
};


/******************************************************************************/
#endif /* OPERATION_H_ */
