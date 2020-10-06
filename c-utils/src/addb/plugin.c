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
  [PEA_GETATTR_RES_RC] = { .str = "get_attribute_result" },
  [PEA_ACCESS_FLAGS] = { .str = "access_flag" },
  [PEA_ACCESS_RES_RC] = { .str = "access_result" },
  [PEA_KVS_ALLOC_SIZE] = { .str = "kvs_alloc_size" },
  [PEA_KVS_ALLOC_RES_RC] = { .str = "kvs_alloc_result" },
  [PEA_DSTORE_GET_RES_RC] = { .str = "dstore_get_result" },
  [PEA_DSTORE_PREAD_OFFSET] = { .str = "dstore_pread_offset" },
  [PEA_DSTORE_PREAD_COUNT] = { .str = "dstore_pread_count" },
  [PEA_DSTORE_PREAD_BS] = { .str = "dstore_pread_bs" },
  [PEA_DSTORE_PREAD_RES_RC] = { .str = "dstore_pread_result" },
  [PEA_KVS_GET_KLEN] = { .str = "kvs_get_key_length" },
  [PEA_KVS_GET_VLEN] = { .str = "kvs_get_value_length" },
  [PEA_KVS_GET_RES_RC] = { .str = "kvs_get_result" },
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
  [PFT_KVS_ALLOC] = { .str = "kvs_alloc" },
  [PFT_KVS_GET] = { .str = "kvs_get" },
  [PFT_CFS_READ] = { .str = "cfs_read" },
  [PFT_CFS_GETATTR] = { .str = "cfs_get_attribute" },
  [PFT_CFS_ACCESS] = { .str = "cfs_access" },
  [PFT_DSTORE_GET] = { .str = "dstore_get" },
  [PFT_DSTORE_PREAD] = { .str = "dstore_pread" },
  [PFT_FSAL_WRITE] = { .str = "fsal_write" },
  [PFT_CFS_WRITE] = { .str = "cfs_write" },
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
            &decode_perfc_entity_attrs
        }
    },
    {
        TSDB_MK_AID(TSDB_MOD_FSUSER, 0xEF),
        "fsuser_map",
        {
            &decode_perfc_function_tags,
            &decode_perfc_entry_type,
            &hex, // operation id
            &hex // mapping with opertation id
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
