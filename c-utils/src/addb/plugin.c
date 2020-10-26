/*
 * Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * For any questions about this software or licensing,
 * please email opensource@seagate.com or cortx-questions@seagate.com.
 *
 */

#include <stdio.h>
#include <string.h>
#include <addb2/plugin_api.h>
#include <operation.h>
#include "perf/perf-counters.h"
#include <lib/assert.h>

#ifndef ARRAY_SIZE
#define ARRAY_SIZE(a) (sizeof(a)/sizeof(a[0]))
#endif

/* Borrowed from addb2/dump.c, hope Motr will publish it as API in future */

static void dec(struct m0_addb2__context *ctx, const uint64_t *v, char *buf)
{
  sprintf(buf, "%" PRId64, v[0]);
}

static void hex(struct m0_addb2__context *ctx, const uint64_t *v, char *buf)
{
  sprintf(buf, "%" PRIx64, v[0]);
}

static void hex0x(struct m0_addb2__context *ctx, const uint64_t *v, char *buf)
{
  sprintf(buf, "0x%" PRIx64, v[0]);
}

static void oct(struct m0_addb2__context *ctx, const uint64_t *v, char *buf)
{
  sprintf(buf, "%" PRIo64, v[0]);
}

static void ptr(struct m0_addb2__context *ctx, const uint64_t *v, char *buf)
{
  sprintf(buf, "@%p", *(void **)v);
}

static void bol(struct m0_addb2__context *ctx, const uint64_t *v, char *buf)
{
  sprintf(buf, "%s", v[0] ? "true" : "false");
}

/* end of clip from dump.c */

static const struct entity_state_items {
  const char* str;
} g_entity_state_items_map[] = {
  [PES_GEN_INIT] = { .str = "init" },
  [PES_GEN_FINI] = { .str = "finish" },
};
_Static_assert(ARRAY_SIZE(g_entity_state_items_map) == PES_END, "Invalid entity state");

static void decode_perfc_entity_states(struct m0_addb2__context *ctx,
                                       const uint64_t *v, char *buf)
{
  M0_PRE(*v < PES_END);
  strcpy(buf, g_entity_state_items_map[*v].str);
}

static const struct entity_attrs_items {
  const char* str;
} g_entity_attrs_items_map[] = {
  [PEA_W_OFFSET] = { .str = "write_offset" },
  [PEA_W_SIZE] = { .str = "write_size" },
  [PEA_W_RES_MAJ] = { .str = "write_result_major_code" },
  [PEA_W_RES_MIN] = { .str = "write_result_minor_code" },

  [PEA_R_OFFSET] = { .str = "read_offset" },
  [PEA_R_IOVC] = { .str = "read_vector_count" },
  [PEA_R_IOVL] = { .str = "read_vector_length" },
  [PEA_R_RES_MAJ] = { .str = "read_result_major_code" },
  [PEA_R_RES_MIN] = { .str = "read_result_minor_code" },

  [PEA_R_C_COUNT] = { .str = "read_cfs_count" },
  [PEA_R_C_OFFSET] = { .str = "read_cfs_offset" },
  [PEA_R_C_RES_RC] = { .str = "read_cfs_result" },

  [PEA_GETATTR_RES_MAJ] = { .str = "get_attribute_result_major_code" },
  [PEA_GETATTR_RES_MIN] = { .str = "get_attribute_result_minor_code" },
  [PEA_GETATTR_RES_RC] = { .str = "get_attribute_result" },

  [PEA_SETATTR_RES_MAJ] = { .str = "set_attribute_result_major_code" },
  [PEA_SETATTR_RES_MIN] = { .str = "set_attribute_result_minor_code" },
  [PEA_SETATTR_RES_RC] = { .str = "set_attribute_result" },

  [PEA_OPEN_RES_MAJ] = { .str = "open_result_major_code" },
  [PEA_OPEN_RES_MIN] = { .str = "open_result_minor_code" },
  [PEA_OPEN_RES_RC] = { .str = "open_result" },

  [PEA_STATUS_RES_RC] = { .str = "status_result" },

  [PEA_CLOSE_RES_MAJ] = { .str = "close_result_major_code" },
  [PEA_CLOSE_RES_MIN] = { .str = "close_result_minor_code" },
  [PEA_CLOSE_RES_RC] = { .str = "close_result" },

  [PEA_REOPEN_RES_MAJ] = { .str = "reopen_result_major_code" },
  [PEA_REOPEN_RES_MIN] = { .str = "reopen_result_minor_code" },
  [PEA_REOPEN_RES_RC] = { .str = "reopen_result" },

  [PEA_ACCESS_FLAGS] = { .str = "access_flag" },
  [PEA_ACCESS_RES_RC] = { .str = "access_result" },

  [PEA_KVS_ALLOC_SIZE] = { .str = "kvs_alloc_size" },
  [PEA_KVS_ALLOC_RES_RC] = { .str = "kvs_alloc_result" },
  [PEA_KVS_KLEN] = { .str = "kvs_key_length" },
  [PEA_KVS_VLEN] = { .str = "kvs_value_length" },
  [PEA_KVS_RES_RC] = { .str = "kvs_result" },

  [PEA_DSTORE_OLD_SIZE] = {.str = "dstore_old_size"},
  [PEA_DSTORE_NEW_SIZE] = {.str = "dstore_new_size"},
  [PEA_DSTORE_GET_RES_RC] = { .str = "dstore_get_result" },
  [PEA_DSTORE_PREAD_OFFSET] = { .str = "dstore_pread_offset" },
  [PEA_DSTORE_PREAD_COUNT] = { .str = "dstore_pread_count" },
  [PEA_DSTORE_PREAD_RES_RC] = { .str = "dstore_pread_result" },
  [PEA_DSTORE_PWRITE_OFFSET] = { .str = "dstore_pwrite_offset" },
  [PEA_DSTORE_PWRITE_COUNT] = { .str = "dstore_pwrite_count" },
  [PEA_DSTORE_PWRITE_RES_RC] = { .str = "dstore_pwrite_result" },
  [PEA_DSTORE_BS] = { .str = "dstore_bs" },

  [PEA_TIME_ATTR_START_OTHER_FUNC] = { .str = "attr_time_start_other_func" },
  [PEA_TIME_ATTR_END_OTHER_FUNC] = { .str = "attr_time_end_other_func" },

  [PEA_TIME_ATTR_START_M0_OBJ_OP] = { .str = "attr_time_start_m0_obj_op" },
  [PEA_TIME_ATTR_END_M0_OBJ_OP] = { .str = "attr_time_end_m0_obj_op" },
  [PEA_TIME_ATTR_START_M0_OP_FINISH] = { .str = "attr_time_start_m0_op_finish" },
  [PEA_TIME_ATTR_END_M0_OP_FINISH] = { .str = "attr_time_end_m0_op_finish" },
  [PEA_TIME_ATTR_START_M0_OP_FREE] = { .str = "attr_time_start_m0_op_free" },
  [PEA_TIME_ATTR_END_M0_OP_FREE] = { .str = "attr_time_end_m0_op_free" },
  [PEA_M0_OP_SM_ID] = { .str = "m0_operation_sm_id" },
  [PEA_M0_OP_SM_STATE] = { .str = "m0_operation_sm_state" },
  [PEA_DSTORE_RES_RC] = { .str = "dstore_result_code" },
  [PEA_NS_RES_RC] = { .str = "ns_result_code" },
  [PEA_KVS_LIST_SIZE] = { .str = "kvs_list_size" },

  [PEA_TIME_ATTR_START_M0_OBJ_INIT] = { .str = "attr_time_start_m0_obj_init" },
  [PEA_TIME_ATTR_END_M0_OBJ_INIT] = { .str = "attr_time_end_m0_obj_init" },
  [PEA_TIME_ATTR_START_M0_OP_LAUNCH] = { .str = "attr_time_start_m0_obj_launch" },
  [PEA_TIME_ATTR_END_M0_OP_LAUNCH] = { .str = "attr_time_end_m0_obj_launch" },
  [PEA_TIME_ATTR_START_M0_OP_WAIT] = { .str = "attr_time_start_m0_obj_wait" },
  [PEA_TIME_ATTR_END_M0_OP_WAIT] = { .str = "attr_time_end_m0_obj_wait" },
  [PEA_TIME_ATTR_START_M0_RC] = { .str = "attr_time_start_m0_obj_rc" },
  [PEA_TIME_ATTR_END_M0_RC] = { .str = "attr_time_end_m0_obj_rc" },
  [PEA_TIME_ATTR_START_M0_ENTITY_CREATE] = { .str = "attr_time_start_m0_entity_create" },
  [PEA_TIME_ATTR_END_M0_ENTITY_CREATE] = { .str = "attr_time_end_m0_entity_create" },
  [PEA_TIME_ATTR_START_M0_ENTITY_DELETE] = { .str = "attr_time_start_m0_entity_delete" },
  [PEA_TIME_ATTR_END_M0_ENTITY_DELETE] = { .str = "attr_time_end_m0_entity_delete" },
  [PEA_TIME_ATTR_START_M0_ENTITY_OPEN] = { .str = "attr_time_start_m0_entity_open" },
  [PEA_TIME_ATTR_END_M0_ENTITY_OPEN] = { .str = "attr_time_end_m0_entity_open" },
  [PEA_TIME_ATTR_START_M0_FREE] = { .str = "attr_time_start_m0_free" },
  [PEA_TIME_ATTR_END_M0_FREE] = { .str = "attr_time_end_m0_free" },
  [PEA_TIME_ATTR_START_M0_ENTITY_FINISH] = { .str = "attr_time_start_m0_entity_finish" },
  [PEA_TIME_ATTR_END_M0_ENTITY_FINISH] = { .str = "attr_time_end_m0_entity_finish" },
  [PEA_TIME_ATTR_START_M0_UFID_NEXT] = { .str = "attr_time_start_m0_ufid_next" },
  [PEA_TIME_ATTR_END_M0_UFID_NEXT] = { .str = "attr_time_end_m0_ufid_next" },
  [PEA_TIME_ATTR_START_M0_ALLOC_PTR] = { .str = "attr_time_start_m0_alloc_ptr" },
  [PEA_TIME_ATTR_END_M0_ALLOC_PTR] = { .str = "attr_time_end_m0_alloc_ptr" },

  [PEA_M0STORE_RES_RC] = { .str = "m0store_result_code" },

  [PEA_TIME_ATTR_START_M0_CLIENT_INIT] = { .str = "attr_time_start_m0_client_init" },
  [PEA_TIME_ATTR_END_M0_CLIENT_INIT] = { .str = "attr_time_end_m0_client_init" },
  [PEA_TIME_ATTR_START_M0_CONTAINER_INIT] = { .str = "attr_time_start_m0_container_init" },
  [PEA_TIME_ATTR_END_M0_CONTAINER_INIT] = { .str = "attr_time_end_m0_container_init" },
  [PEA_TIME_ATTR_START_M0_FID_SSCANF] = { .str = "attr_time_start_m0_fid_sscanf" },
  [PEA_TIME_ATTR_END_M0_FID_SSCANF] = { .str = "attr_time_end_m0_fid_sscanf" },
  [PEA_TIME_ATTR_START_M0_FID_PRINT] = { .str = "attr_time_start_m0_fid_print" },
  [PEA_TIME_ATTR_END_M0_FID_PRINT] = { .str = "attr_time_end_m0_fid_print" },
  [PEA_TIME_ATTR_START_M0_IDX_INIT] = { .str = "attr_time_start_m0_idx_init" },
  [PEA_TIME_ATTR_END_M0_IDX_INIT] = { .str = "attr_time_end_m0_idx_init" },
  [PEA_TIME_ATTR_START_M0_UFID_INIT] = { .str = "attr_time_start_m0_ufid_init" },
  [PEA_TIME_ATTR_END_M0_UFID_INIT] = { .str = "attr_time_end_m0_ufid_init" },
  [PEA_INIT_MOTR_RES_RC] = { .str = "m0_init_motr_result_code" },

  [PEA_TIME_ATTR_START_M0_IDX_OP] = { .str = "attr_time_start_m0_idx_op" },
  [PEA_TIME_ATTR_END_M0_IDX_OP] = { .str = "attr_time_end_m0_idx_op" },
  [PEA_TIME_ATTR_START_M0_IDX_FINISH] = { .str = "attr_time_start_m0_idx_finish" },
  [PEA_TIME_ATTR_END_M0_IDX_FINISH] = { .str = "attr_time_end_m0_idx_finish" },

  [PEA_M0KVS_RES_RC] = { .str = "m0kvs_result_code" },

  [PEA_CFS_CREATE_PARENT_INODE] = { .str = "cfs_create_parent_inode" },
  [PEA_CFS_NEW_FILE_INODE] = { .str = "cfs_create_file_inode" },
  [PEA_CFS_RES_RC] = { .str = "cfs_result_rc" },

};
_Static_assert(ARRAY_SIZE(g_entity_attrs_items_map) == PEA_END, "Invalid entity attribute");

static void decode_perfc_entity_attrs(struct m0_addb2__context *ctx,
                                      const uint64_t *v, char *buf)
{
  M0_PRE(*v < PEA_END);
  strcpy(buf, g_entity_attrs_items_map[*v].str);
}

static const struct function_tag_items {
  const char* str;
} g_function_tag_items_map[] = {
  [PFT_FSAL_READ] = { .str = "fsal_read" },
  [PFT_FSAL_WRITE] = { .str = "fsal_write" },
  [PFT_FSAL_GETATTRS] = { .str = "fsal_getattrs" },
  [PFT_FSAL_SETATTRS] = { .str = "fsal_setattrs" },
  [PFT_FSAL_MKDIR] = { .str = "fsal_mkdir" },
  [PFT_FSAL_READDIR] = { .str = "fsal_readdir" },
  [PFT_FSAL_RMDIR] = { .str = "fsal_rmdir" },
  [PFT_FSAL_LOOKUP] = { .str = "fsal_lookup" },
  [PFT_FSAL_OPEN] = { .str = "fsal_open" },
  [PFT_FSAL_STATUS] = { .str = "fsal_status" },
  [PFT_FSAL_CLOSE] = { .str = "fsal_close" },
  [PFT_FSAL_REOPEN] = { .str = "fsal_reopen" },
  [PFT_FSAL_COMMIT] = { .str = "fsal_commit" },

  [PFT_KVS_INIT] = { .str = "kvs_init" },
  [PFT_KVS_FINI] = { .str = "kvs_finish" },
  [PFT_KVS_ALLOC] = { .str = "kvs_alloc" },
  [PFT_KVS_FREE] = { .str = "kvs_free" },
  [PFT_KVS_GET] = { .str = "kvs_get" },
  [PFT_KVS_SET] = { .str = "kvs_set" },
  [PFT_KVTREE_ITER_CH] = { .str = "kvtree_iterate_child" },

  [PFT_CFS_READ] = { .str = "cfs_read" },
  [PFT_CFS_WRITE] = { .str = "cfs_write" },
  [PFT_CFS_GETATTR] = { .str = "cfs_get_attribute" },
  [PFT_CFS_SETATTR] = { .str = "cfs_set_attribute" },
  [PFT_CFS_ACCESS] = { .str = "cfs_access" },
  [PFT_CFS_MKDIR] = { .str = "cfs_mkdir" },
  [PFT_CFS_RMDIR] = { .str = "cfs_rmdir" },
  [PFT_CFS_READDIR] = { .str = "cfs_readdir" },
  [PFT_CFS_LOOKUP] = { .str = "cfs_lookup" },
  [PFT_CFS_FILE_OPEN] = { .str = "cfs_open" },
  [PFT_CFS_FILE_CLOSE] = { .str = "cfs_close" },
  [PFT_CFS_CREATE_EX] = { .str = "cfs_create_ex" },
  [PFT_CFS_CREATE] = { .str = "cfs_create" },

  [PFT_DSTORE_GET] = { .str = "dstore_get" },
  [PFT_DSTORE_PREAD] = { .str = "dstore_pread" },
  [PFT_DSTORE_PWRITE] = { .str = "dstore_pwrite" },

  [PFT_DS_INIT] = { .str = "ds_init" },
  [PFT_DS_FINISH] = { .str = "ds_finish" },

  [PFT_DS_OBJ_GET_ID] = { .str = "ds_obj_get_id" },
  [PFT_DS_OBJ_CREATE] = { .str = "ds_obj_create" },
  [PFT_DS_OBJ_DELETE] = { .str = "ds_obj_delete" },
  [PFT_DS_OBJ_ALLOC] = { .str = "ds_obj_alloc" },
  [PFT_DS_OBJ_FREE] = { .str = "ds_obj_free" },
  [PFT_DS_OBJ_OPEN] = { .str = "ds_obj_open" },
  [PFT_DS_OBJ_CLOSE] = { .str = "ds_obj_close" },

  [PFT_DS_IO_INIT] = { .str = "ds_io_init" },
  [PFT_DS_IO_SUBMIT] = { .str = "ds_io_submit" },
  [PFT_DS_IO_WAIT] = { .str = "ds_io_wait" },
  [PFT_DS_IO_FINISH] = { .str = "ds_io_finish" },

  [PFT_DSTORE_INIT] = { .str = "dstore_init"},
  [PFT_DSTORE_FINI] = { .str = "dstore_fini"},
  [PFT_DSTORE_OBJ_CREATE] = { .str = "dstore_obj_create"},
  [PFT_DSTORE_OBJ_DELETE] = { .str = "dstore_obj_delete"},
  [PFT_DSTORE_OBJ_SHRINK] = { .str = "dstore_obj_shrink"},
  [PFT_DSTORE_OBJ_RESIZE] = { .str = "dstore_obj_resize"},
  [PFT_DSTORE_GET_NEW_OBJID] = { .str = "dstore_get_new_objid"},
  [PFT_DSTORE_OBJ_OPEN] = { .str = "dstore_obj_open"},
  [PFT_DSTORE_OBJ_CLOSE] = { .str = "dstore_obj_close"},
  [PFT_DSTORE_IO_OP_INIT_AND_SUBMIT] = 
	{ .str = "dstore_io_op_init_and_submit"},
  [PFT_DSTORE_IO_OP_WRITE] = { .str = "dstore_io_op_write"},
  [PFT_DSTORE_IO_OP_READ] = { .str = "dstore_io_op_read"},
  [PFT_DSTORE_IO_OP_WAIT] = { .str = "dstore_io_op_wait"},
  [PFT_DSTORE_IO_OP_FINI] = { .str = "dstore_io_op_fini"},

  [PFT_CORTX_KVS_INIT] = { .str = "cortx_kvs_init" },
  [PFT_CORTX_KVS_FINISH] = { .str = "cortx_kvs_finish" },
  [PFT_CORTX_KVS_ALLOC] = { .str = "cortx_kvs_alloc" },
  [PFT_CORTX_KVS_FREE] = { .str = "cortx_kvs_free" },
  [PFT_CORTX_KVS_INDEX_CREATE] = { .str = "cortx_kvs_index_create" },
  [PFT_CORTX_KVS_INDEX_DELETE] = { .str = "cortx_kvs_index_delete" },
  [PFT_CORTX_KVS_INDEX_OPEN] = { .str = "cortx_kvs_index_open" },
  [PFT_CORTX_KVS_INDEX_CLOSE] = { .str = "cortx_kvs_index_close" },
  [PFT_CORTX_KVS_GET_BIN] = { .str = "cortx_kvs_get_bin" },
  [PFT_CORTX_KVS4_GET_BIN] = { .str = "cortx_kvs4_get_bin" },
  [PFT_CORTX_KVS_SET_BIN] = { .str = "cortx_kvs_set_bin" },
  [PFT_CORTX_KVS4_SET_BIN] = { .str = "cortx_kvs4_set_bin" },
  [PFT_CORTX_KVS_DELETE_BIN] = { .str = "cortx_kvs_delete_bin" },
  [PFT_CORTX_KVS_GEN_FID] = { .str = "cortx_kvs_gen_fid" },
  [PFT_CORTX_KVS_PREFIX_ITER_FIND] = { .str = "cortx_kvs_prefix_iter_find" },
  [PFT_CORTX_KVS_PREFIX_ITER_NEXT] = { .str = "cortx_kvs_prefix_iter_next" },
  [PFT_CORTX_KVS_PREFIX_ITER_FINISH] = { .str = "cortx_kvs_prefix_iter_finish" },
  [PFT_CORTX_KVS_ITER_GET_KV] = { .str = "cortx_kvs_iter_get_kv" },
  [PFT_CORTX_KVS_GET_LIST_SIZE] = { .str = "cortx_kvs_get_list_size" },

  [PFT_M0_INIT] = { .str = "m0_init" },
  [PFT_M0_FINISH] = { .str = "m0_finish" },
  [PFT_M0STORE_CREATE_OBJECT] = { .str = "m0store_create_object" },
  [PFT_M0STORE_DELETE_OBJECT] = { .str = "m0store_delete_object" },
  [PFT_M0STORE_OPEN_ENTITY] = { .str = "m0store_open_entity" },
  [PFT_M0STORE_OBJ_OPEN] = { .str = "m0store_obj_open" },
  [PFT_M0STORE_OBJ_CLOSE] = { .str = "m0store_obj_close" },
  [PFT_M0_UFID_GET] = { .str = "m0_ufid_get" },

  [PFT_INIT_MOTR] = { .str = "m0_init_motr" },

  [PFT_M0KVS_REINIT] = { .str = "m0kvs_reinit" },
  [PFT_M0_OP_KVS] = { .str = "m0_op_kvs" },
  [PFT_M0IDX_CREATE] = { .str = "m0idx_create" },
  [PFT_M0IDX_DELETE] = { .str = "m0idx_delete" },
  [PFT_M0IDX_OPEN] = { .str = "m0idx_open" },
  [PFT_M0IDX_CLOSE] = { .str = "m0idx_close" },
  [PFT_M0_OP2_KVS] = { .str = "m0_op2_kvs" },
  [PFT_M0KVS_GET] = { .str = "m0kvs_get" },
  [PFT_M0KVS4_GET] = { .str = "m0kvs4_get" },
  [PFT_M0KVS4_SET] = { .str = "m0kvs4_set" },
  [PFT_M0KVS_SET] = { .str = "m0kvs_set" },
  [PFT_M0KVS_DELETE] = { .str = "m0kvs_delete" },
  [PFT_M0KVS_IDX_GEN_FID] = { .str = "m0kvs_idx_gen_fid" },
  [PFT_M0KVS_LIST_SET] = { .str = "m0kvs_list_set" },
  [PFT_M0KVS_LIST_GET] = { .str = "m0kvs_list_get" },
  [PFT_M0KVS_PATTERN] = { .str = "m0kvs_pattern" },
  [PFT_M0KVS_KEY_PREFIX_EXISTS] = { .str = "m0kvs_key_prefix_exists" },
  [PFT_M0KVS_KEY_ITER_FINISH] = { .str = "m0kvs_key_iter_finish" },
  [PFT_M0KVS_KEY_ITER_FIND] = { .str = "m0kvs_key_iter_find" },
  [PFT_M0KVS_KEY_ITER_NEXT] = { .str = "m0kvs_key_iter_next" },
  [PFT_M0KVS_ALLOC] = { .str = "m0kvs_alloc" },
  [PFT_M0KVS_FREE] = { .str = "m0kvs_free" },

  [PFT_M0_KEY_ITER_FINISH] = { .str = "m0_key_iter_finish" },
  [PFT_M0_KEY_ITER_FIND] = { .str = "m0_key_iter_find" },
  [PFT_M0_KEY_ITER_NEXT] = { .str = "m0_key_iter_next" },

  [PFT_OPEN2_BY_HANDLE] = { .str = "open2_by_handle" },
  [PFT_FILE_STATE_OPEN] = { .str = "file_state_open" },
  [PFT_SHARE_TRY_NEW_STATE] = { .str = "share_try_new_state" },
  [PFT_OPEN2_BY_NAME] = { .str = "open2_by_name" },
  [PFT_CREATE_UNCHECKED] = { .str = "create_uncheck" },

};
_Static_assert(ARRAY_SIZE(g_function_tag_items_map) == PFT_END, "Invalid function tag");

static void decode_perfc_function_tags(struct m0_addb2__context *ctx,
                                       const uint64_t *v, char *buf)
{
  M0_PRE(*v < PFT_END);
  strcpy(buf, g_function_tag_items_map[*v].str);
}

static const struct entry_type_items {
  const char* str;
} g_entry_type_items_map[] = {
  [PET_STATE] = { .str = "state" },
  [PET_ATTR] = { .str = "attribute" },
  [PET_MAP] = { .str = "map" },
};
_Static_assert(ARRAY_SIZE(g_entry_type_items_map) == PET_END, "Invalid entry type");

static void decode_perfc_entry_type(struct m0_addb2__context *ctx,
                                    const uint64_t *v, char *buf)
{
  M0_PRE(*v < PET_END);
  strcpy(buf, g_entry_type_items_map[*v].str);
}

static struct m0_addb2__id_intrp gs_curr_ids[] = {
    {
        TSDB_MK_AID(TSDB_MOD_FSUSER, 0xAB),
        "fsuser_state",
        {
            &decode_perfc_function_tags,
            &decode_perfc_entry_type,
            &hex, // operation id
            &decode_perfc_entity_states
        }
    },
    {
        TSDB_MK_AID(TSDB_MOD_FSUSER, 0xCD),
        "fsuser_attribute",
        {
            &decode_perfc_function_tags,
            &decode_perfc_entry_type,
            &hex, // operation id
            &decode_perfc_entity_attrs,
            &hex // attribute val
        }
    },
    {
        TSDB_MK_AID(TSDB_MOD_FSUSER, 0xEF),
        "fsuser_map",
        {
            &decode_perfc_function_tags,
            &decode_perfc_entry_type,
            &hex, // map name
            &hex, // operation id
            &hex, // mapping with origin operation id
            &hex // mapping with caller operation id
        }
    },

    {0}
};

int m0_addb2_load_interps(uint64_t flags,
                          struct m0_addb2__id_intrp **intrps_array)
{
  /* suppres "unused" warnings */
  (void)dec;
  (void)hex0x;
  (void)oct;
  (void)hex;
  (void)bol;
  (void)ptr;

  *intrps_array = gs_curr_ids;
  return 0;
}
