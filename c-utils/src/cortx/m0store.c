/*
 * Filename:         m0store.c
 * Description:      Contains motr related IO operations
 *                   which use motr objects.
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

#include "m0common.h"
#include "common/log.h" /* log_* */
#include "common/helpers.h" /* RC_* */
#include "debug.h" /* dassert */
#include "object.h" /* obj_id_t */
#include "operation.h"
#include <cfs_utils_perfc.h>

/* Open a motr entity.
 * @param[in] - A pointer to motr entity to be opened
 * @return    - 0 on success and on failure returns the same
 *              error code given by underlyig storage API
*/
static int open_entity(struct m0_entity *entity)
{
	int rc = 0;
	struct m0_op *ops[1] = {NULL};

	perfc_trace_inii(PFT_M0STORE_OPEN_ENTITY, PEM_NFS_TO_MOTR);
	dassert(entity);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_OPEN);
	RC_WRAP_LABEL(rc, out, m0_entity_open, entity, &ops[0]);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_OPEN);
	dassert(ops[0] != NULL);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(ops, 1);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	RC_WRAP_LABEL(rc, out, m0_op_wait, ops[0],
		      M0_BITS(M0_OS_FAILED, M0_OS_STABLE),
		      M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);

	perfc_trace_attr(PEA_M0_OP_SM_ID, ops[0]->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, ops[0]->op_sm.sm_state);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_RC);
	RC_WRAP_LABEL(rc, out, m0_rc, ops[0]);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_RC);

out:
	if (rc) {
		RC_WRAP_SET(rc);
	}

	if (ops[0]) {
		m0_op_fini(ops[0]);
		m0_op_free(ops[0]);
	}
	perfc_trace_attr(PEA_M0STORE_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

/* Create a motr object
 * @param[in] - FID for the objct to be created
 * @return    - 0 on success and on failure returns the same
 *              error code given by underlyig storage API
*/
int m0store_create_object(struct m0_uint128 id)
{
	int    rc;
	struct m0_obj obj;
	struct m0_op *ops[1] = {NULL};

	perfc_trace_inii(PFT_M0STORE_CREATE_OBJECT, PEM_NFS_TO_MOTR);
	if (!my_init_done)
		m0kvs_reinit();

	memset(&obj, 0, sizeof(struct m0_obj));

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OBJ_INIT);
	m0_obj_init(&obj, &motr_uber_realm, &id,
                m0_client_layout_id(motr_instance));
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OBJ_INIT);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_CREATE);
	RC_WRAP_LABEL(rc, out, m0_entity_create, NULL, &obj.ob_entity,
                  &ops[0]);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_CREATE);
	dassert(ops[0] != NULL);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(ops, ARRAY_SIZE(ops));
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	RC_WRAP_LABEL(rc, cleanup, m0_op_wait, ops[0],
		      M0_BITS(M0_OS_FAILED, M0_OS_STABLE),
		      M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);

	perfc_trace_attr(PEA_M0_OP_SM_ID, ops[0]->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, ops[0]->op_sm.sm_state);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_RC);
	RC_WRAP_LABEL(rc, cleanup, m0_rc, ops[0]);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_RC);

cleanup:
	if (ops[0]) {
		m0_op_fini(ops[0]);
		m0_op_free(ops[0]);
		m0_entity_fini(&obj.ob_entity);
	}

out:
	log_debug("fid = "U128X_F" rc=%d", U128_P(&id), rc);
	perfc_trace_attr(PEA_M0STORE_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

/* Delete a motr object
 * @param[in] - FID of the objct to be deleted
 * @return    - 0 on success and on failure returns the same
 *              error code given by underlyig storage API
*/
int m0store_delete_object(struct m0_uint128 id)
{
	int    rc;
	struct m0_obj obj;
	struct m0_op *ops[1] = {NULL};

	perfc_trace_inii(PFT_M0STORE_DELETE_OBJECT, PEM_NFS_TO_MOTR);
	if (!my_init_done)
		m0kvs_reinit();

	memset(&obj, 0, sizeof(struct m0_obj));

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OBJ_INIT);
	m0_obj_init(&obj, &motr_uber_realm, &id,
		    m0_client_layout_id(motr_instance));
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OBJ_INIT);

	RC_WRAP_LABEL(rc, out, open_entity, &obj.ob_entity);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_DELETE);
	RC_WRAP_LABEL(rc, out, m0_entity_delete, &obj.ob_entity,
		      &ops[0]);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_DELETE);
	dassert(ops[0] != NULL);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(ops, ARRAY_SIZE(ops));
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	RC_WRAP_LABEL(rc, out, m0_op_wait, ops[0],
		      M0_BITS(M0_OS_FAILED, M0_OS_STABLE),
		      M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);

	perfc_trace_attr(PEA_M0_OP_SM_ID, ops[0]->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, ops[0]->op_sm.sm_state);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_RC);
	RC_WRAP_LABEL(rc, out, m0_rc, ops[0]);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_RC);

out:
	if (ops[0]) {
		m0_op_fini(ops[0]);
		m0_op_free(ops[0]);
		m0_entity_fini(&obj.ob_entity);
	}

	log_debug("fid = "U128X_F" rc=%d", U128_P(&id), rc);
	perfc_trace_attr(PEA_M0STORE_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0_ufid_get(struct m0_uint128 *ufid)
{
	int		  rc;

	perfc_trace_inii(PFT_M0_UFID_GET, PEM_M0_TO_MOTR);
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_UFID_NEXT);
	rc = m0_ufid_next(&ufid_generator, 1, ufid);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_UFID_NEXT);
	perfc_trace_attr(PEA_M0STORE_RES_RC, rc);
	if (rc != 0) {
		log_err("Failed to generate a ufid: %d\n", rc);
		return rc;
	}
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return 0;
}

int m0_fid_to_string(struct m0_uint128 *fid, char *fid_s)
{
	int rc;

	rc = m0_fid_print(fid_s, KVS_FID_STR_LEN, (struct m0_fid *)fid);
	if (rc < 0) {
		log_err("Failed to generate fid str, rc=%d", rc);
		return rc;
	}

	log_info("fid=%s", fid_s);
	/* rc is a buffer length, therefore it should also count '\0' */
	return rc + 1 /* '\0' */;
}

ssize_t m0store_get_bsize(struct m0_uint128 id)
{
	return m0_obj_layout_id_to_unit_size(
					     m0_client_layout_id(
					     motr_instance));
}

/*****************************************************************************/
int m0store_obj_open(const obj_id_t *id, struct m0_obj *pobj)
{
	int rc;
	struct m0_op *op = NULL;
	struct m0_uint128 fid;

    perfc_trace_inii(PFT_M0STORE_OBJ_OPEN, PEM_NFS_TO_MOTR);
	dassert(id);
	dassert(pobj);

	fid = M0_UINT128(id->f_hi, id->f_lo);

	M0_SET0(pobj);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OBJ_INIT);
	m0_obj_init(pobj, &motr_uber_realm, &fid,
		    m0_client_layout_id(motr_instance));
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OBJ_INIT);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_OPEN);
	rc = m0_entity_open(&pobj->ob_entity, &op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_OPEN);
	if (rc) {
		RC_WRAP_SET(rc);
		goto out;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(&op, 1);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

    perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	rc = m0_op_wait(op, M0_BITS(M0_OS_FAILED,
                    M0_OS_STABLE),
                    M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);
	perfc_trace_attr(PEA_M0_OP_SM_ID, op->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, op->op_sm.sm_state);
	if (rc) {
		RC_WRAP_SET(rc);
		goto out;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_RC);
	rc = m0_rc(op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_RC);
	if (rc) {
		RC_WRAP_SET(rc);
		goto out;
	}

out:
	if (op) {
		m0_op_fini(op);
		m0_op_free(op);
	}

	log_debug("open (%p, " U128X_F "," OBJ_ID_F "), rc=%d",
		  pobj, U128_P(&pobj->ob_entity.en_id), OBJ_ID_P(id), rc);
	perfc_trace_attr(PEA_M0STORE_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

void m0store_obj_close(struct m0_obj *obj)
{
	perfc_trace_inii(PFT_M0STORE_OBJ_CLOSE, PEM_NFS_TO_MOTR);
	dassert(obj);

	log_debug("close (%p, " U128X_F ")", obj,
		  U128_P(&obj->ob_entity.en_id));
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_FINISH);
	m0_entity_fini(&obj->ob_entity);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_FINISH);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
}

/*****************************************************************************/
