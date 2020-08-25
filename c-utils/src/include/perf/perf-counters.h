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



/******************************************************************************/
#endif /* PERF_COUNTERS_H_ */
