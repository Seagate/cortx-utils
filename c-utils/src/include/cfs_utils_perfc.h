/*
 * Filename:	cfs_utils_perfc.h
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

#ifndef __CFS_UTILS_PERF_COUNTERS_H_
#define __CFS_UTILS_PERF_COUNTERS_H_
/******************************************************************************/
#include "perf/tsdb.h" /* ACTION_ID_BASE */
#include "operation.h"
#include <pthread.h>
#include <string.h>
#include "debug.h"
#include "perf/perf-counters.h"

enum perfc_utils_function_tags {
	PFT_M0_START = PFTR_RANGE_5_START,

	PFT_M0_INIT,
	PFT_M0_FINISH,
	PFT_M0STORE_CREATE_OBJECT,
	PFT_M0STORE_DELETE_OBJECT,
	PFT_M0STORE_OPEN_ENTITY,
	PFT_M0STORE_OBJ_OPEN,
	PFT_M0STORE_OBJ_CLOSE,
	PFT_M0_UFID_GET,

	PFT_INIT_MOTR,

	PFT_M0KVS_REINIT,
	PFT_M0_OP_KVS,
	PFT_M0IDX_CREATE,
	PFT_M0IDX_DELETE,
	PFT_M0IDX_OPEN,
	PFT_M0IDX_CLOSE,
	PFT_M0_OP2_KVS,
	PFT_M0KVS_GET,
	PFT_M0KVS4_GET,
	PFT_M0KVS4_SET,
	PFT_M0KVS_SET,
	PFT_M0KVS_DELETE,
	PFT_M0KVS_IDX_GEN_FID,
	PFT_M0KVS_LIST_SET,
	PFT_M0KVS_LIST_GET,
	PFT_M0KVS_PATTERN,
	PFT_M0KVS_KEY_PREFIX_EXISTS,
	PFT_M0KVS_KEY_ITER_FINISH,
	PFT_M0KVS_KEY_ITER_FIND,
	PFT_M0KVS_KEY_ITER_NEXT,
	PFT_M0KVS_ALLOC,
	PFT_M0KVS_FREE,

	PFT_M0_END = PFTR_RANGE_5_END
};

enum perfc_utils_entity_attrs {
	PEA_M0_START = PEAR_RANGE_5_START,

	PEA_TIME_ATTR_START_M0_OP_FINISH,
	PEA_TIME_ATTR_END_M0_OP_FINISH,
	PEA_TIME_ATTR_START_M0_OP_FREE,
	PEA_TIME_ATTR_END_M0_OP_FREE,
	PEA_M0_OP_SM_ID,
	PEA_M0_OP_SM_STATE,

	PEA_TIME_ATTR_START_M0_OBJ_INIT,
	PEA_TIME_ATTR_END_M0_OBJ_INIT,
	PEA_TIME_ATTR_START_M0_OP_LAUNCH,
	PEA_TIME_ATTR_END_M0_OP_LAUNCH,
	PEA_TIME_ATTR_START_M0_OP_WAIT,
	PEA_TIME_ATTR_END_M0_OP_WAIT,
	PEA_TIME_ATTR_START_M0_RC,
	PEA_TIME_ATTR_END_M0_RC,
	PEA_TIME_ATTR_START_M0_ENTITY_CREATE,
	PEA_TIME_ATTR_END_M0_ENTITY_CREATE,
	PEA_TIME_ATTR_START_M0_ENTITY_DELETE,
	PEA_TIME_ATTR_END_M0_ENTITY_DELETE,
	PEA_TIME_ATTR_START_M0_ENTITY_OPEN,
	PEA_TIME_ATTR_END_M0_ENTITY_OPEN,
	PEA_TIME_ATTR_START_M0_ENTITY_FINISH,
	PEA_TIME_ATTR_END_M0_ENTITY_FINISH,
	PEA_TIME_ATTR_START_M0_UFID_NEXT,
	PEA_TIME_ATTR_END_M0_UFID_NEXT,
	PEA_M0STORE_RES_RC,

	PEA_TIME_ATTR_START_M0_CLIENT_INIT,
	PEA_TIME_ATTR_END_M0_CLIENT_INIT,
	PEA_TIME_ATTR_START_M0_CONTAINER_INIT,
	PEA_TIME_ATTR_END_M0_CONTAINER_INIT,
	PEA_TIME_ATTR_START_M0_FID_SSCANF,
	PEA_TIME_ATTR_END_M0_FID_SSCANF,
	PEA_TIME_ATTR_START_M0_FID_PRINT,
	PEA_TIME_ATTR_END_M0_FID_PRINT,
	PEA_TIME_ATTR_START_M0_IDX_INIT,
	PEA_TIME_ATTR_END_M0_IDX_INIT,
	PEA_TIME_ATTR_START_M0_UFID_INIT,
	PEA_TIME_ATTR_END_M0_UFID_INIT,
	PEA_INIT_MOTR_RES_RC,

	PEA_TIME_ATTR_START_M0_IDX_OP,
	PEA_TIME_ATTR_END_M0_IDX_OP,
	PEA_TIME_ATTR_START_M0_IDX_FINISH,
	PEA_TIME_ATTR_END_M0_IDX_FINISH,

	PEA_M0KVS_RES_RC,

	PEA_M0_END = PEAR_RANGE_5_END
};

enum perfc_utils_entity_maps {
	PEM_M0_START = PEMR_RANGE_5_START,

	PEM_NFS_TO_MOTR,
	PEM_M0_TO_MOTR,

	PEM_M0_END = PEMR_RANGE_5_END
};

/******************************************************************************/
#endif /* __CFS_UTILS_PERF_COUNTERS_H_ */
