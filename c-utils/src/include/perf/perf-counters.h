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


/* TODO: move it into submodules */

enum perfc_cfs {
	PERFC_CFS_MKDIR,
};

enum perfc_nsal {
	PERFC_NSAL_GET,
	PERFC_NSAL_SET,
	PERFC_NSAL_LISTCB,
	PERFC_NSAL_DEL,
};

enum perfc_m0_adapter {
	/* EE points */
	PERFC_M0A_GET,
	PERFC_M0A_PUT,
	PERFC_M0A_NEXT,
	PERFC_M0A_DEL,

	PERFC_M0A_OBJ_CREATE,
	PERFC_M0A_OBJ_DELETE,
	PERFC_M0A_OBJ_OPEN,
	PERFC_M0A_OBJ_CLOSE,

	PERFC_M0A_IDX_CREATE,
	PERFC_M0A_IDX_DELETE,
	PERFC_M0A_IDX_OPEN,
	PERFC_M0A_IDX_CLOSE,

	/* Mappings */
	PERFC_M0A_MAP_GET,
	PERFC_M0A_MAP_PUT,
	PERFC_M0A_MAP_NEXT,
	PERFC_M0A_MAP_DEL,
};

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

enum perfc_function_tags {
	PFT_START,

	PFT_FSAL_READ,
	PFT_FSAL_WRITE,
	PFT_FSAL_GETATTRS,
	PFT_FSAL_SETATTRS,
	PFT_FSAL_MKDIR,
	PFT_FSAL_RMDIR,
	PFT_FSAL_READDIR,
	PFT_FSAL_LOOKUP,

	PFT_KVS_INIT,
	PFT_KVS_FINI,
	PFT_KVS_ALLOC,
	PFT_KVS_FREE,
	PFT_KVS_GET,
	PFT_KVS_SET,
	PFT_KVTREE_ITER_CH,

	PFT_CFS_READ,
	PFT_CFS_WRITE,
	PFT_CFS_GETATTR,
	PFT_CFS_SETATTR,
	PFT_CFS_ACCESS,
	PFT_CFS_MKDIR,
	PFT_CFS_RMDIR,
	PFT_CFS_READDIR,
	PFT_CFS_LOOKUP,

	PFT_DSTORE_GET,
	PFT_DSTORE_PREAD,
	PFT_DSTORE_PWRITE,

	PFT_END
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

enum perfc_entity_attrs {
	PEA_START,

	PEA_W_OFFSET,
	PEA_W_SIZE,
	PEA_W_RES_MAJ,
	PEA_W_RES_MIN,

	PEA_R_OFFSET,
	PEA_R_IOVC,
	PEA_R_IOVL,
	PEA_R_RES_MAJ,
	PEA_R_RES_MIN,

	PEA_R_C_COUNT,
	PEA_R_C_OFFSET,
	PEA_R_C_RES_RC,

	PEA_GETATTR_RES_MAJ,
	PEA_GETATTR_RES_MIN,
	PEA_GETATTR_RES_RC,

	PEA_SETATTR_RES_MAJ,
	PEA_SETATTR_RES_MIN,
	PEA_SETATTR_RES_RC,

	PEA_ACCESS_FLAGS,
	PEA_ACCESS_RES_RC,

	PEA_KVS_ALLOC_SIZE,
	PEA_KVS_ALLOC_RES_RC,

	PEA_DSTORE_GET_RES_RC,

	PEA_DSTORE_PREAD_OFFSET,
	PEA_DSTORE_PREAD_COUNT,
	PEA_DSTORE_PREAD_RES_RC,

	PEA_DSTORE_PWRITE_OFFSET,
	PEA_DSTORE_PWRITE_COUNT,
	PEA_DSTORE_PWRITE_RES_RC,

	PEA_DSTORE_BS,

	PEA_KVS_KLEN,
	PEA_KVS_VLEN,
	PEA_KVS_RES_RC,

	PEA_OTHER_FUNC_CALL,
	PEA_OTHER_FUNC_END,

	PEA_END
};

enum perfc_entity_maps {
	PEM_START,

	PEM_UNUSED,

	PEM_NFS_TO_CFS,
	PEM_NFS_TO_DSAL,
	PEM_NFS_TO_NSAL,
	PEM_NFS_TO_MOTR,

	PEM_CFS_TO_NFS,
	PEM_CFS_TO_DSAL,
	PEM_CFS_TO_NSAL,
	PEM_CFS_TO_MOTR,

	PEM_DSAL_TO_NFS,
	PEM_DSAL_TO_CFS,
	PEM_DSAL_TO_MOTR,

	PEM_NSAL_TO_NFS,
	PEM_NSAL_TO_CFS,
	PEM_NSAL_TO_MOTR,

	PEM_KVS_TO_NFS,
	PEM_DSTORE_TO_NFS,

	PEM_END
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
 * | tsdb_modules | function tag | map tag | src opid | dst opid | [Rest] |
 * where Arguments:
 *	- TSDB Module ID
 *	- an enum value from perfc_function_tags
 *	- PET_MAP tag as this traces a map of two ops
 *	- Caller passed map tag from enum perfc_entity_maps
 *	- opid - caller generated tag for operation id
 *	- related_opid - caller generated tag for related operation id
 *	- __VA_ARGS_ - attribute-specific arguments.
 */
#define PERFC_MAP_V2(__mod, __fn_tag, map_tag, opid, related_opid, ...) do {\
	dassert(__fn_tag > PFT_START && __fn_tag < PFT_END);		\
	dassert(map_tag > PEM_START && map_tag < PEM_END);		\
	TSDB_ADD(TSDB_MK_AID(__mod, 0xEF), __fn_tag, PET_MAP, map_tag,	\
		 opid, related_opid, __VA_ARGS__);			\
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

	if (perfstack == NULL) {
	    return ptctx;
	}

	if (perfstack->top == -1) {
	    return ptctx;
	}

	return perfstack->pstack[perfstack->top];
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
	dassert(ptctx.opid != PERFC_INVALID_ID);			\
	if (ptctx.opid != PERFC_INVALID_ID) {				\
		PERFC_MAP_V2(ptctx.mod, fn_tag, map_tag, _opid,		\
			     ptctx.opid, __VA_ARGS__);			\
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
