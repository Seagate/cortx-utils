/*
 * Filename:	perf-counters.h
 * Description:	This module defines performance counters and helpers.
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

#ifndef PERF_COUNTERS_H_
#define PERF_COUNTERS_H_
/******************************************************************************/
#include "perf/tsdb.h" /* ACTION_ID_BASE */
#include "operation.h"
#include <pthread.h>
#include <string.h>
#include "debug.h"

/******************************************************************************/
/** Subtags for entry/exit points and mappings. */
enum perfc_subtags {
	PERFC_EE_OP_BEGIN = 0xB,
	PERFC_EE_OP_END = 0xE,
	PERFC_EE_OP_PUSH = 0x1,
	PERFC_EE_OP_POP = 0x2,
	PERFC_MAP = 0xF,
};

/** Creates a unique id for a function (or any other "action"). */
#define TSDB_MK_AID(__mod_id, __tag) \
	(TSDB_ACTION_ID_BASE + ((__mod_id) << 12 | (__tag)))

/* Format of Entry/Exit points:
 * | <AID> | <EE type> | <Call ID> | [Rest] |
 * where
 *	- AID - action id (function id)
 *	- EE type - begin/end/push/pop
 *	- Call ID - id the particular call
 *	- Rest - operation-specific arguments.
 *
 * Arguments:
 *	__mod - Module ID (hardcoded).
 *	__fn  - Function ID (hardcoded).
 *	__call - Call ID (generated).
 *	__VA_ARGS_ - Optional arguments.
 */
#define PERFC_OP_EE(__mod, __fn, __call, __ee_type, ...)			\
	TSDB_ADD(TSDB_MK_AID(__mod, __fn), __ee_type , __call,	\
		 __VA_ARGS__)


/* Format of mappings :
 * | <AID> | MAP | <Call ID> | <MAP-ID> | <EXTERNAL-ID> |
 * where
 *	AID - action id (function id)
 *	MAP - constant (PERFC_MAP)
 *	MAP-ID - id of the mapping.
 *	Call ID - id the particular call to AID
 *	EXTERNAL-ID - id of the foreign operation (M0, XID, etc).
 * This structure forms the following mapping:
 *	<MAP-ID> : KEY -> EXTERNAL-ID
 *	where KEY is a combination of function id and call id.
 */

#define PERFC_MAP(__mod_id, __fn, __call, __map_id, __ext_id, ...) \
	TSDB_ADD(TSDB_MK_AID(__mod_id, __fn), PERFC_MAP,  __call, \
		 __map_id, __ext_id, __VA_ARGS__)


#define PERFC_INVALID_ID 0
extern uint64_t perfc_id_gen;
extern pthread_key_t perfc_tls_key;

struct perfc_tls_ctx {
	uint8_t mod;
	uint64_t opid;
	uint16_t fn_tag;
	uint16_t map_tag;
};

#define MAX_PERFC_STACK_DEPTH 16
struct perfc_callstack {
	uint8_t mod;
	int8_t top;
	struct perfc_tls_ctx pstack[MAX_PERFC_STACK_DEPTH];
};

enum perfc_entry_type {
	PET_START,

	PET_STATE,
	PET_ATTR,
	PET_MAP,

	PET_END
};

enum perfc_entity_states {
	PES_START,

	PES_GEN_INIT,
	PES_GEN_FINI,

	PES_END
};

enum perfc_function_tags_ranges {
	PFTR_START,
	PFTR_RANGE_1_START = 1U,	/* Reserved for cortxfs*/
	PFTR_RANGE_1_END = 256U,
	PFTR_RANGE_2_START = 257U,	/* Reserved for cortx-fs-ganesha*/
	PFTR_RANGE_2_END = 512U,
	PFTR_RANGE_3_START = 513U,	/* Reserved for dsal*/
	PFTR_RANGE_3_END = 768U,
	PFTR_RANGE_4_START = 769U,	/* Reserved for nsal*/
	PFTR_RANGE_4_END = 1024U,
	PFTR_RANGE_5_START = 1025U,	/* Reserved for utils*/
	PFTR_RANGE_5_END = 1280U,
	PFTR_RANGE_6_START = 1281U,	/* Reserved for future repos*/
	PFTR_RANGE_6_END = 1537U,
	PFTR_END
};

enum perfc_entity_attrs_ranges {
	PEAR_START,
	PEAR_RANGE_1_START = 1U,	/* Reserved for cortxfs*/
	PEAR_RANGE_1_END = 256U,
	PEAR_RANGE_2_START = 257U,	/* Reserved for cortx-fs-ganesha*/
	PEAR_RANGE_2_END = 512U,
	PEAR_RANGE_3_START = 513U,	/* Reserved for dsal*/
	PEAR_RANGE_3_END = 768U,
	PEAR_RANGE_4_START = 769U,	/* Reserved for nsal*/
	PEAR_RANGE_4_END = 1024U,
	PEAR_RANGE_5_START = 1025U,	/* Reserved for utils*/
	PEAR_RANGE_5_END = 1280U,
	PEAR_RANGE_6_START = 1281U,	/* Reserved for future repos*/
	PEAR_RANGE_6_END = 1537U,
	PEAR_END
};

enum perfc_entity_maps_ranges {
	PEMR_START,
	PEMR_RANGE_1_START = 1U,	/* Reserved for cortxfs*/
	PEMR_RANGE_1_END = 256U,
	PEMR_RANGE_2_START = 257U,	/* Reserved for cortx-fs-ganesha*/
	PEMR_RANGE_2_END = 512U,
	PEMR_RANGE_3_START = 513U,	/* Reserved for dsal*/
	PEMR_RANGE_3_END = 768U,
	PEMR_RANGE_4_START = 769U,	/* Reserved for nsal*/
	PEMR_RANGE_4_END = 1024U,
	PEMR_RANGE_5_START = 1025U,	/* Reserved for utils*/
	PEMR_RANGE_5_END = 1280U,
	PEMR_RANGE_6_START = 1281U,	/* Reserved for future repos*/
	PEMR_RANGE_6_END = 1537U,
	PEMR_END
};

/* Format of State perf. counters:
 * | tsdb_modules | function tag | PET_STATE | opid | perfc_entity_states
 * | [Rest] |
 * where Arguments:
 *	- TSDB Module ID
 *	- an enum value from perfc_function_tags
 *	- PET_STATE tag as this traces a state
 *	- op id - caller generated tag for operation id
 *	- perfc_entity_states - caller generated enum value from
 *	  perfc_entity_states to tag the state
 *	- __VA_ARGS_ - operation-specific arguments.
 */
#define PERFC_STATE_V2(__mod, __fn_tag, opid, state, ...) do {		\
	dassert(__fn_tag > PFT_START && __fn_tag < PFT_END);		\
	dassert(state > PES_START && state < PES_END);			\
	TSDB_ADD(TSDB_MK_AID(__mod, 0xAB), __fn_tag, PET_STATE, opid,	\
		 state, __VA_ARGS__);					\
} while (0)

/* Format of Attribute perf. counters:
 * | tsdb_modules | function tag | PET_ATTR | opid | attr type | attrid
 * | [Rest] |
 * where Arguments:
 *	- TSDB Module ID
 *	- an enum value from perfc_function_tags
 *	- PET_ATTR tag as this traces an attribute of a op
 *	- op id - caller generated tag for operation id
 *	- perfc_entity_attrs - caller generated enum value from
 *	  perfc_entity_attrs to tag the attribute
 *	- __VA_ARGS_ - attribute-specific arguments.
 */
#define PERFC_ATTR_V2(__mod, __fn_tag, opid, attrid, ...) do {		\
	dassert(__fn_tag > PFT_START && __fn_tag < PFT_END);		\
	dassert(attrid > PEA_START && attrid < PEA_END);		\
	TSDB_ADD(TSDB_MK_AID(__mod, 0xCD), __fn_tag, PET_ATTR, opid,	\
		 attrid, __VA_ARGS__);					\
} while (0)

/* Format of Map perf. counters:
 * | tsdb_modules | function tag | map tag | src opid | dst opid | caller_opid, [Rest] |
 * where Arguments:
 *	- TSDB Module ID
 *	- an enum value from perfc_function_tags
 *	- PET_MAP tag as this traces a map of two ops
 *	- Caller passed map tag from enum perfc_entity_maps
 *	- opid - caller generated tag for operation id
 *	- related_opid - caller generated tag for related operation id
 *	- caller_opid - caller generated tag for previous caller's operation id
 *	- __VA_ARGS_ - attribute-specific arguments.
 */
#define PERFC_MAP_V2(__mod, __fn_tag, map_tag, opid, related_opid, caller_opid,...) do {\
	dassert(__fn_tag > PFT_START && __fn_tag < PFT_END);		\
	dassert(map_tag > PEM_START && map_tag < PEM_END);		\
	TSDB_ADD(TSDB_MK_AID(__mod, 0xEF), __fn_tag, PET_MAP, map_tag,	\
		 opid, related_opid, caller_opid, __VA_ARGS__);			\
} while (0)

#ifdef ENABLE_TSDB_ADDB

static inline uint64_t perf_id_gen(void)
{
	return __sync_add_and_fetch(&perfc_id_gen, 1);
}

#define perfc_tls_push(_ptc) do {					\
	struct perfc_callstack *perfstack =				\
		pthread_getspecific(perfc_tls_key);			\
	if (perfstack) {						\
		_ptc.mod = perfstack->mod;				\
		dassert(perfstack->top < MAX_PERFC_STACK_DEPTH - 1);	\
		perfstack->pstack[++perfstack->top] = _ptc;		\
	}								\
} while (0)

#define perfc_tls_pop(_ptc) do {					\
	struct perfc_callstack *perfstack =				\
		pthread_getspecific(perfc_tls_key);			\
	if (perfstack) {						\
		if (perfstack->top != -1) {				\
			_ptc = perfstack->pstack[perfstack->top--];	\
		} else {						\
			_ptc.opid = PERFC_INVALID_ID;			\
		}							\
	}								\
} while (0)

#define perfc_tls_ini(_mod, _opid, _fn_tag) do {			\
	int rc;								\
	struct perfc_tls_ctx ptc;					\
	struct perfc_callstack *perfstack =				\
				alloca(sizeof (struct perfc_callstack));\
	dassert(perfstack != NULL);					\
	perfstack->mod = _mod;						\
	perfstack->top = -1;						\
	rc = pthread_setspecific(perfc_tls_key, perfstack);		\
	dassert(rc != NULL);						\
	ptc.mod = _mod;							\
	ptc.opid = _opid;						\
	ptc.fn_tag = _fn_tag;						\
	ptc.map_tag = PEM_UNUSED;					\
	perfc_tls_push(ptc);						\
} while (0)

#define perfc_tls_fini() do {						\
	int rc;								\
	rc = pthread_setspecific(perfc_tls_key, NULL);			\
	dassert(rc != NULL);						\
} while (0)

static inline struct perfc_tls_ctx perfc_tls_get_origin(void)
{
	struct perfc_tls_ctx ptctx = {.opid = PERFC_INVALID_ID};
	struct perfc_callstack *perfstack = pthread_getspecific(perfc_tls_key);

	if (perfstack == NULL) {
	    return ptctx;
	}

	if (perfstack->top == -1) {
	    return ptctx;
	}

	return perfstack->pstack[0];
}

static inline struct perfc_tls_ctx perfc_tls_get_top(void)
{
	struct perfc_tls_ctx ptctx = {.opid = PERFC_INVALID_ID};
	struct perfc_callstack *perfstack = pthread_getspecific(perfc_tls_key);

	if ((perfstack == NULL) || (perfstack->top == -1)) {
	    return ptctx;
	}

	return perfstack->pstack[perfstack->top];
}

static inline struct perfc_tls_ctx perfc_tls_get_prev(void)
{
	struct perfc_tls_ctx ptctx = {.opid = PERFC_INVALID_ID};
	struct perfc_callstack *perfstack = pthread_getspecific(perfc_tls_key);

	if ((perfstack == NULL) || (perfstack->top == -1)) {
	    return ptctx;
	}

	if (perfstack->top == 0) {
	    return perfstack->pstack[perfstack->top];
	}

	return perfstack->pstack[perfstack->top-1];
}

#define perfc_trace_state(state, ...) do {				\
	struct perfc_tls_ctx ptctx = perfc_tls_get_top();		\
	if (ptctx.opid != PERFC_INVALID_ID) {				\
		PERFC_STATE_V2(ptctx.mod, ptctx.fn_tag,			\
			       ptctx.opid, state, __VA_ARGS__);		\
	}								\
} while (0)

#define perfc_trace_attr(attrid, ...) do {				\
	struct perfc_tls_ctx ptctx = perfc_tls_get_top();		\
	if (ptctx.opid != PERFC_INVALID_ID) {				\
		PERFC_ATTR_V2(ptctx.mod, ptctx.fn_tag,			\
			      ptctx.opid, attrid, __VA_ARGS__);		\
	}								\
} while (0)

#define perfc_trace_map(fn_tag, map_tag, _opid, ...) do {		\
	struct perfc_tls_ctx ptctx = perfc_tls_get_origin();		\
	struct perfc_tls_ctx ptcctx = perfc_tls_get_prev();		\
	dassert(ptctx.opid != PERFC_INVALID_ID);			\
	dassert(ptcctx.opid != PERFC_INVALID_ID);			\
	if (ptctx.opid != PERFC_INVALID_ID) {				\
		PERFC_MAP_V2(ptctx.mod, fn_tag, map_tag, _opid,		\
			     ptctx.opid, ptcctx.opid, __VA_ARGS__);	\
	}								\
} while (0)

#define perfc_trace_ini(ptc) do {					\
	struct perfc_callstack *pstack = pthread_getspecific(perfc_tls_key);\
	if (pstack) {							\
		dassert(ptc.opid != PERFC_INVALID_ID);			\
		ptc.mod = pstack->mod;					\
		perfc_tls_push(ptc);					\
		perfc_trace_state(PES_GEN_INIT);			\
		perfc_trace_map(ptc.fn_tag, ptc.map_tag, ptc.opid);	\
	}								\
} while (0)

#define PERFC_TLS_POP_VERIFY 1U
#define PERFC_TLS_POP_DONT_VERIFY 2U

#define perfc_trace_fini(_ptc, verify) do {				\
	struct perfc_tls_ctx ptc;					\
	perfc_trace_state(PES_GEN_FINI);				\
	perfc_tls_pop(ptc);						\
	if (verify == PERFC_TLS_POP_VERIFY) {				\
		dassert(memcmp(&ptc, &_ptc, sizeof(ptc)) == 0);		\
	}								\
} while (0)

#define perfc_trace_inii(_fn_tag, _map_tag) 				\
	struct perfc_tls_ctx ptc;					\
	ptc.opid = perf_id_gen();					\
	dassert(ptc.opid != PERFC_INVALID_ID);				\
	ptc.fn_tag = _fn_tag;						\
	ptc.map_tag = _map_tag;						\
	perfc_trace_ini(ptc);						\

#define perfc_trace_finii(verify) perfc_trace_fini(ptc, verify)

#else

static inline uint64_t perf_id_gen(void)
{
	return PERFC_INVALID_ID;
}

#define perfc_tls_push(...)

#define perfc_tls_pop(...)

#define perfc_tls_ini(...)

#define perfc_tls_fini(...)

static inline struct perfc_tls_ctx perfc_tls_get_origin(void)
{
	struct perfc_tls_ctx ptctx = {.opid = PERFC_INVALID_ID};
	return ptctx;
}

static inline struct perfc_tls_ctx perfc_tls_get_top(void)
{
	struct perfc_tls_ctx ptctx = {.opid = PERFC_INVALID_ID};
	return ptctx;
}

#define perfc_trace_state(...)

#define perfc_trace_attr(...)

#define perfc_trace_map(...)

#define perfc_trace_ini(...)

#define perfc_trace_fini(...)

#define perfc_trace_inii(...)

#define perfc_trace_finii(...)

#endif /*  ENABLE_TSDB_ADDB */

/******************************************************************************/
#endif /* PERF_COUNTERS_H_ */
