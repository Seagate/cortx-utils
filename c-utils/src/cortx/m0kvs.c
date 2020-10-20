/*
 * Filename:         m0kvs.c
 * Description:      Contains motr related kv operations
 *                   which use motr index.
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
#include "addb2/global.h" /* global_leave */
#include "common/log.h"
#include <debug.h>
#include "perf/tsdb.h"
#include "operation.h"

int m0kvs_reinit(void)
{
	int rc;
	perfc_trace_inii(PFT_M0KVS_REINIT, PEM_NFS_TO_MOTR);
	rc = m0init(conf);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

void m0kvs_do_init(void)
{
	int rc;

	rc = get_motr_conf(conf);

	if (rc != 0) {
		log_err("Invalid config file\n");
		exit(1);
	}

	log_config();

	/*  TODO: Create a config file parameter. */
	tsdb_init(true, true);

	rc = init_motr();
	assert(rc == 0);

	motr_init_done = true;
	m0init_thread = pthread_self();

	/* TODO:
	 * This is a workaround for the situation where
	 * m0init is called from a thread thr1 that is blocked on
	 * another thread thr2 which is the thread where m0fini is called.
	 * This situation causes a panic in M0 code because ADDB is not aware
	 * of such sophisticated condition.
	 * thr1:
	 *	m0init()
	 *	spawn thr2
	 *	block on thr2
	 * thr2:
	 *	do_smth()
	 *	m0fini()
	 *
	 * The thread_leave() call tells ADDB to "forget" about thr1,
	 * so that thr2 can successfully conclude m0fini without panics.
	 *
	 * This call removes the ability to gather ADDB traces from this
	 * thread. The caller is responsible to restoring the ADDB
	 * context after m0init is done.
	 */
	m0_addb2_global_thread_leave();
}


static int m0_op_kvs(enum m0_idx_opcode opcode,
		     struct m0_bufvec *key,
		     struct m0_bufvec *val)
{
	struct m0_op	 *op = NULL;
	int rcs[1];
	int rc;

	perfc_trace_inii(PFT_M0_OP_KVS, PEM_NFS_TO_MOTR);
	if (!my_init_done)
		m0kvs_reinit();

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_OP);
	rc = m0_idx_op(&idx, opcode, key, val,
		       rcs, M0_OIF_OVERWRITE, &op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_OP);
	if (rc) {
		perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
		perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
		return rc;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(&op, 1);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	rc = m0_op_wait(op, M0_BITS(M0_OS_STABLE),
			M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);

	perfc_trace_attr(PEA_M0_OP_SM_ID, op->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, op->op_sm.sm_state);

	if (rc)
		goto out;

	/* Check rcs array even if op is succesful */
	rc = rcs[0];

out:
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FINISH);
	m0_op_fini(op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FINISH);

	/* it seems like 0_free(&op) is not needed */
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0idx_create(const struct m0_uint128 *fid, struct m0_idx **index)
{
        int                     rc;
	struct m0_op    *op = NULL;
	struct m0_idx   *idx = NULL;

	*index = NULL;

	perfc_trace_inii(PFT_M0IDX_CREATE, PEM_NFS_TO_MOTR);
	idx = m0kvs_alloc(sizeof(struct m0_idx));
	if (idx == NULL) {
		rc = -ENOMEM;
		goto out;
	}

	/* Set an index creation operation. */
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_INIT);
	m0_idx_init(idx,
		    &motr_container.co_realm, (struct m0_uint128 *)fid);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_INIT);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_CREATE);
	rc = m0_entity_create(NULL, &(idx->in_entity), &op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_CREATE);
	if (rc == 0) {
 		/* Launch and wait for op to complete */
		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
		m0_op_launch(&op, 1);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
		rc = m0_op_wait(op,
                        M0_BITS(M0_OS_FAILED,
                        M0_OS_STABLE),
                        M0_TIME_NEVER);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);

		perfc_trace_attr(PEA_M0_OP_SM_ID, op->op_sm.sm_id);
		perfc_trace_attr(PEA_M0_OP_SM_STATE, op->op_sm.sm_state);
		if (rc == 0) {
			rc = op->op_rc;
		}
	}

	/* fini and release */
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FINISH);
	m0_op_fini(op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FINISH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FREE);
	m0_op_free(op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FREE);

	if (rc) {
		m0kvs_free(idx);
	} else {
		*index = idx;
	}

out:
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0idx_delete(const struct m0_uint128 *fid)
{
	int rc;
	struct m0_op     *op = NULL;
	struct m0_idx    idx;

	perfc_trace_inii(PFT_M0IDX_DELETE, PEM_NFS_TO_MOTR);
	memset(&idx, 0, sizeof(struct m0_idx));

	/* Set an index creation operation. */
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_INIT);
	m0_idx_init(&idx,
                &motr_container.co_realm, (struct m0_uint128 *)fid);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_INIT);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_OPEN);
	rc = m0_entity_open(&idx.in_entity, &op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_OPEN);

	if (rc != 0) {
		goto out;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_ENTITY_DELETE);
	rc = m0_entity_delete(&(idx.in_entity), &op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_ENTITY_DELETE);
	if (rc == 0) {
		/* Launch and wait for op to complete */
		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
		m0_op_launch(&op, 1);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
		rc = m0_op_wait(op,
                        M0_BITS(M0_OS_FAILED,
                        M0_OS_STABLE),
                        M0_TIME_NEVER);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);
		perfc_trace_attr(PEA_M0_OP_SM_ID, op->op_sm.sm_id);
		perfc_trace_attr(PEA_M0_OP_SM_STATE, op->op_sm.sm_state);
		if (rc == 0) {
			rc = op->op_rc;
		}
	}

	/* fini and release */
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FINISH);
	m0_op_fini(op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FINISH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FREE);
	m0_op_free(op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FREE);

out:
	m0_entity_fini(&(idx.in_entity));
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0idx_open(const struct m0_uint128 *fid, struct m0_idx **index)
{
	int 			rc = 0;
	struct m0_idx  	*idx = NULL;

	perfc_trace_inii(PFT_M0IDX_OPEN, PEM_NFS_TO_MOTR);
	*index = NULL;

	if (!my_init_done)
		m0kvs_reinit();

	idx = m0kvs_alloc(sizeof(struct m0_idx));
	if (idx == NULL) {
		rc = -ENOMEM;
		goto out;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_INIT);
	m0_idx_init(idx, &motr_container.co_realm,
                (struct m0_uint128 *)fid);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_INIT);

	*index = idx;

out:
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

void m0idx_close(struct m0_idx *index)
{
	perfc_trace_inii(PFT_M0IDX_CLOSE, PEM_NFS_TO_MOTR);
	if (!my_init_done)
		m0kvs_reinit();
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_FINISH);
	m0_idx_fini(index);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_FINISH);
	m0kvs_free(index);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
}

static int m0_op2_kvs(void *ctx,
		      enum m0_idx_opcode opcode,
		      struct m0_bufvec *key,
		      struct m0_bufvec *val)
{
	struct m0_op	 *op = NULL;
	int rcs[1];
	int rc;

	struct m0_idx     *index = NULL;

	perfc_trace_inii(PFT_M0_OP2_KVS, PEM_NFS_TO_MOTR);

	if (!my_init_done)
		m0kvs_reinit();

	index = ctx;

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_OP);
	rc = m0_idx_op(index, opcode, key, val,
		       rcs, M0_OIF_OVERWRITE, &op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_OP);

	if (rc) {
		perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
		perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
		return rc;
    }

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(&op, 1);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	rc = m0_op_wait(op,
                    M0_BITS(M0_OS_FAILED,
                    M0_OS_STABLE),
                    M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);
	perfc_trace_attr(PEA_M0_OP_SM_ID, op->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, op->op_sm.sm_state);
	if (rc)
		goto out;

	/* Check rcs array even if op is succesful */
	rc = rcs[0];

out:
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FINISH);
	m0_op_fini(op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FINISH);
	/* it seems like 0_free(&op) is not needed */
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_get(void *ctx, void *k, size_t klen,
	       void **v, size_t *vlen)
{
	m0_bcount_t k_len = klen;
	struct m0_bufvec key, val;
	int rc;

	perfc_trace_inii(PFT_M0KVS_GET, PEM_NFS_TO_MOTR);

	// @todo: Assert is called when NFS Ganesha is run.
	// Once issue is debugged uncomment the M0_DASSERT call.
	if (!my_init_done)
		m0kvs_reinit();
	//M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(v, vlen);

	rc = m0_op2_kvs(ctx, M0_IC_GET, &key, &val);
	if (rc != 0)
		goto out;

out:
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs4_get(void *k, size_t klen,
	       void **v, size_t *vlen)
{
	m0_bcount_t k_len = klen;
	struct m0_bufvec key, val;
	int rc;

	perfc_trace_inii(PFT_M0KVS4_GET, PEM_NFS_TO_MOTR);

	// @todo: Assert is called when NFS Ganesha is run.
	// Once issue is debugged uncomment the M0_DASSERT call.
	if (!my_init_done)
		m0kvs_reinit();
	//M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(v, vlen);

	rc = m0_op_kvs(M0_IC_GET, &key, &val);
	if (rc != 0)
		goto out;

out:
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs4_set(void *k, const size_t klen,
	       void *v, const size_t vlen)
{
	m0_bcount_t k_len = klen;
	m0_bcount_t v_len = vlen;
	struct m0_bufvec key, val;
	int rc;

	perfc_trace_inii(PFT_M0KVS4_SET, PEM_NFS_TO_MOTR);

	M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(&v, &v_len);

	rc = m0_op_kvs(M0_IC_PUT, &key, &val);

	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_set(void *ctx, void *k, const size_t klen,
	       void *v, const size_t vlen)
{
	m0_bcount_t k_len = klen;
	m0_bcount_t v_len = vlen;
	struct m0_bufvec key, val;
	int rc;

    perfc_trace_inii(PFT_M0KVS_SET, PEM_NFS_TO_MOTR);

	M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(&v, &v_len);

	rc = m0_op2_kvs(ctx, M0_IC_PUT, &key, &val);

	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_del(void *ctx, void *k, const size_t klen)
{
	struct m0_bufvec key;
	m0_bcount_t k_len = klen;
	int rc;

	perfc_trace_inii(PFT_M0KVS_DELETE, PEM_NFS_TO_MOTR);

	M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);

	rc = m0_op2_kvs(ctx, M0_IC_DEL, &key, NULL);

	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_idx_gen_fid(struct m0_uint128 *index_fid)
{
	int rc = 0;

	perfc_trace_inii(PFT_M0KVS_IDX_GEN_FID, PEM_NFS_TO_MOTR);
	perfc_trace_attr(PEA_TIME_ATTR_START_M0_UFID_NEXT);
	rc = m0_ufid_next(&ufid_generator, 1, index_fid);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_UFID_NEXT);
	if (rc != 0) {
		log_err("Failed to generate a ufid: %d\n", rc);
		goto out;
	}

	struct m0_fid tfid = M0_FID_TINIT('x', index_fid->u_hi, index_fid->u_lo);
	index_fid->u_hi = tfid.f_container;
	index_fid->u_lo = tfid.f_key;;

out:
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_list_set(void *ctx, struct m0kvs_list *key,
                   struct m0kvs_list *val)
{
	int rc;

	perfc_trace_inii(PFT_M0KVS_LIST_SET, PEM_NFS_TO_MOTR);

	rc = m0_op2_kvs(ctx, M0_IC_PUT, &key->buf, &val->buf);

	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_list_get(void *ctx, struct m0kvs_list *key,
                   struct m0kvs_list *val)
{
	int rc;

	perfc_trace_inii(PFT_M0KVS_LIST_GET, PEM_NFS_TO_MOTR);

	rc = m0_op2_kvs(ctx, M0_IC_GET, &key->buf, &val->buf);

	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_pattern(void *ctx, char *k, char *pattern,
		    get_list_cb cb, void *arg_cb)
{
	struct m0_bufvec          keys;
	struct m0_bufvec          vals;
	struct m0_op       *op = NULL;
	struct m0_idx      *index = ctx;
	int i = 0;
	int rc;
	int rcs[1];
	bool stop = false;
	char myk[KLEN];
	bool startp = false;
	int size = 0;
	int flags;

	perfc_trace_inii(PFT_M0KVS_PATTERN, PEM_NFS_TO_MOTR);

	strcpy(myk, k);
	flags = 0; /* Only for 1st iteration */

	do {
		/* Iterate over all records in the index. */
		rc = m0_bufvec_alloc(&keys, 1, KLEN);
		if (rc != 0) {
			perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
			perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
			return rc;
		}

		rc = m0_bufvec_alloc(&vals, 1, VLEN);
		if (rc != 0) {
			m0_bufvec_free(&keys);
			perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
			perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
			return rc;
		}

		/* FIXME: Memory leak? check m0_bufvec_alloc
		 * documentation. We don't need to allocate
		 * the buffer twice.
		 */
		keys.ov_buf[0] = m0_alloc(strnlen(myk, KLEN)+1);
		keys.ov_vec.v_count[0] = strnlen(myk, KLEN)+1;
		strcpy(keys.ov_buf[0], myk);

		perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_OP);
		rc = m0_idx_op(index, M0_IC_NEXT, &keys, &vals,
		               rcs, flags, &op);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_OP);

		if (rc != 0) {
			m0_bufvec_free(&keys);
			m0_bufvec_free(&vals);
			perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
			perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
			return rc;
		}
		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
		m0_op_launch(&op, 1);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
		rc = m0_op_wait(op,
                        M0_BITS(M0_OS_FAILED,
                        M0_OS_STABLE),
                        M0_TIME_NEVER);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);
		perfc_trace_attr(PEA_M0_OP_SM_ID, op->op_sm.sm_id);
		perfc_trace_attr(PEA_M0_OP_SM_STATE, op->op_sm.sm_state);
		/* @todo : Why is op null after this call ??? */

		if (rc != 0) {
			m0_bufvec_free(&keys);
			m0_bufvec_free(&vals);
			perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
			perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
			return rc;
		}

		if (rcs[0] == -ENOENT) {
			m0_bufvec_free(&keys);
			m0_bufvec_free(&vals);

			/* No more keys to be found */
			if (startp)
				return 0;
			return -ENOENT;
		}
		for (i = 0; i < keys.ov_vec.v_nr; i++) {
			if (keys.ov_buf[i] == NULL) {
				stop = true;
				break;
			}

			/* Small state machine to display things
			 * (they are sorted) */
			if (!fnmatch(pattern, (char *)keys.ov_buf[i], 0)) {

				/* Avoid last one and use it as first
				 *  of next pass */
				if (!stop) {
					if (!cb((char *)keys.ov_buf[i],
						arg_cb))
						break;
				}
				if (startp == false)
					startp = true;
			} else {
				if (startp == true) {
					stop = true;
					break;
				}
			}

			strcpy(myk, (char *)keys.ov_buf[i]);
			flags = M0_OIF_EXCLUDE_START_KEY;
		}

		m0_bufvec_free(&keys);
		m0_bufvec_free(&vals);
	} while (!stop);

	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return size;
}

int m0kvs_key_prefix_exists(void *ctx,
			    const void *kprefix, size_t klen,
			    bool *result)
{
	struct m0_bufvec keys;
	struct m0_bufvec vals;
	struct m0_op *op = NULL;
	struct m0_idx *index = ctx;
	int rc;
	int rcs[1];

	perfc_trace_inii(PFT_M0KVS_KEY_PREFIX_EXISTS, PEM_NFS_TO_MOTR);

	rc = m0_bufvec_alloc(&keys, 1, klen);
	if (rc != 0) {
		goto out;
	}

	rc = m0_bufvec_empty_alloc(&vals, 1);
	if (rc != 0) {
		goto out_free_keys;
	}

	memset(keys.ov_buf[0], 0, keys.ov_vec.v_count[0]);
	memcpy(keys.ov_buf[0], kprefix, klen);

    perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_OP);
	rc = m0_idx_op(index, M0_IC_NEXT, &keys, &vals,
		       rcs, 0, &op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_OP);

	if (rc != 0) {
		goto out_free_vals;
	}

	if (rcs[0] != 0) {
		goto out_free_vals;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(&op, 1);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	rc = m0_op_wait(op,
                    M0_BITS(M0_OS_FAILED,
                    M0_OS_STABLE),
                    M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);
	perfc_trace_attr(PEA_M0_OP_SM_ID, op->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, op->op_sm.sm_state);
	if (rc != 0) {
		goto out_free_op;
	}

	if (rcs[0] == 0) {
		/* The next key cannot be longer than the starting
		 * key by the definition of lexicographical comparison
		 */
		M0_DASSERT(keys.ov_vec.v_count[0] >= klen);
		/* Check if the next key has the same prefix */
		*result = memcmp(kprefix, keys.ov_buf[0], klen) == 0;
		rc = 0;
	} else if (rcs[0] == -ENOENT) {
		*result = false;
		rc = 0;
	} else {
		rc = rcs[0];
	}

out_free_op:
	if (op) {
		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FINISH);
		m0_op_fini(op);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FINISH);

		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FREE);
		m0_op_free(op);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FREE);
	}
out_free_vals:
	m0_bufvec_free(&vals);
out_free_keys:
	m0_bufvec_free(&keys);
out:
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

/** Allocate an empty bufvec.
 * Allocates internal buffers (to data) inside the bufvec
 * without allocating m0_bufvec::ov_buf and m0_bufvec::ov_bec::v_count.
 */
int m0kvs_bufvec_alloc_data(struct m0_bufvec *bufvec)
{
	dassert(bufvec->ov_buf);
	dassert(bufvec->ov_vec.v_count);

	//@todo: need to allocate ov_buf array elements with a given size

	return 0;
}

/** Make a non-empty bufvec to be an empty bufvec.
 * Frees internal buffers (to data) inside the bufvec
 * without freeing m0_bufvec::ov_buf and m0_bufvec::ov_bec::v_count.
 */
static void m0kvs_bufvec_free_data(struct m0_bufvec *bufvec)
{
	uint32_t i;

	dassert(bufvec->ov_buf);

	for (i = 0; i < bufvec->ov_vec.v_nr; ++i) {
		dassert(bufvec->ov_buf[i]);
		m0_free(bufvec->ov_buf[i]);
		bufvec->ov_buf[i] = NULL;
	}
}

void m0kvs_key_iter_fini(struct m0kvs_key_iter *priv)
{
	perfc_trace_inii(PFT_M0KVS_KEY_ITER_FINISH, PEM_NFS_TO_MOTR);

	if (!priv->initialized)
		goto out;

	m0_bufvec_free(&priv->key);
	m0_bufvec_free(&priv->val);

	if (priv->op) {
		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FINISH);
		m0_op_fini(priv->op);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FINISH);

		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FREE);
		m0_op_free(priv->op);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FREE);
	}
out:
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return;
}

int m0kvs_key_iter_find(const void* prefix, size_t prefix_len,
                        struct m0kvs_key_iter *priv)
{
	struct m0_bufvec *key = &priv->key;
	struct m0_bufvec *val = &priv->val;
	struct m0_op **op = &priv->op;
	struct m0_idx *index = priv->index;
	int rc;

	perfc_trace_inii(PFT_M0KVS_KEY_ITER_FIND, PEM_NFS_TO_MOTR);

	if (prefix_len == 0)
		rc = m0_bufvec_empty_alloc(key, 1);
	else
		rc = m0_bufvec_alloc(key, 1, prefix_len);
	if (rc != 0) {
		goto out;
	}

	rc = m0_bufvec_empty_alloc(val, 1);
	if (rc != 0) {
		goto out_free_key;
	}

	memcpy(priv->key.ov_buf[0], prefix, prefix_len);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_OP);
	rc = m0_idx_op(index, M0_IC_NEXT, &priv->key, &priv->val,
                   priv->rcs, 0, op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_OP);

	if (rc != 0) {
		goto out_free_val;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(op, 1);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	rc = m0_op_wait(*op,
                    M0_BITS(M0_OS_FAILED,
                    M0_OS_STABLE),
                    M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);
	perfc_trace_attr(PEA_M0_OP_SM_ID, (*op)->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, (*op)->op_sm.sm_state);
	if (rc != 0) {
		goto out_free_op;
	}

	if (priv->rcs[0] != 0) {
		rc = priv->rcs[0];
		goto out_free_op;
	}

	/* release objects back to priv */
	key = NULL;
	val = NULL;
	op = NULL;
	priv->initialized = true;

out_free_op:
	if (op && *op) {
        perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FINISH);
		m0_op_fini(*op);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FINISH);

		perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_FREE);
		m0_op_free(*op);
		perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_FREE);
	}

out_free_val:
	if (val)
		m0_bufvec_free(val);
out_free_key:
	if (key)
		m0_bufvec_free(key);
out:
	if (rc != 0) {
		memset(priv, 0, sizeof(*priv));
	}

	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

int m0kvs_key_iter_next(struct m0kvs_key_iter *priv)
{
	struct m0_idx *index = priv->index;
	int rc = 0;

	perfc_trace_inii(PFT_M0KVS_KEY_ITER_NEXT, PEM_NFS_TO_MOTR);

	dassert(priv->initialized);

	/* Motr API: "'vals' vector ... should contain NULLs" */
	m0kvs_bufvec_free_data(&priv->val);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_IDX_OP);
	rc = m0_idx_op(index, M0_IC_NEXT,
				   &priv->key, &priv->val, priv->rcs,
				   M0_OIF_EXCLUDE_START_KEY, &priv->op);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_IDX_OP);

	if (rc != 0) {
		goto out;
	}

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_LAUNCH);
	m0_op_launch(&priv->op, 1);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_LAUNCH);

	perfc_trace_attr(PEA_TIME_ATTR_START_M0_OP_WAIT);
	rc = m0_op_wait(priv->op,
                    M0_BITS(M0_OS_FAILED,
                    M0_OS_STABLE),
                    M0_TIME_NEVER);
	perfc_trace_attr(PEA_TIME_ATTR_END_M0_OP_WAIT);
	perfc_trace_attr(PEA_M0_OP_SM_ID, priv->op->op_sm.sm_id);
	perfc_trace_attr(PEA_M0_OP_SM_STATE, priv->op->op_sm.sm_state);
	if (rc != 0) {
		goto out;
	}

	rc = priv->rcs[0];

out:
	perfc_trace_attr(PEA_M0KVS_RES_RC, rc);
	perfc_trace_finii(PERFC_TLS_POP_DONT_VERIFY);
	return rc;
}

void m0kvs_key_iter_get_kv(struct m0kvs_key_iter *priv, void **key,
                           size_t *klen, void **val, size_t *vlen)
{
	struct m0_bufvec *k = &priv->key;
	struct m0_bufvec *v = &priv->val;
	*key = k->ov_buf[0];
	*klen = k->ov_vec.v_count[0];
	*val = v->ov_buf[0];
	*vlen = v->ov_vec.v_count[0];
}

void *m0kvs_alloc(uint64_t size)
{
	return m0_alloc(size);
}

void m0kvs_free(void *ptr)
{
	return m0_free(ptr);
}

int m0kvs_list_alloc(struct m0kvs_list *kvs_list, uint32_t list_cnt)
{
	return m0_bufvec_empty_alloc(&kvs_list->buf, list_cnt);
}

void m0kvs_list_free(struct m0kvs_list *kvs_list)
{
	m0_bufvec_free(&kvs_list->buf);
}

int m0kvs_list_add(struct m0kvs_list *kvs_list, void *buf, size_t len,
                   int pos)
{
	int rc = 0;

	dassert(kvs_list->buf.ov_buf);
	dassert(kvs_list->buf.ov_vec.v_count);

	if (pos >= kvs_list->buf.ov_vec.v_nr)
		return -ENOMEM;

	dassert(kvs_list->buf.ov_vec.v_count[pos] == 0);
	dassert(kvs_list->buf.ov_buf[pos] == NULL);

	kvs_list->buf.ov_vec.v_count[pos] = len;
	kvs_list->buf.ov_buf[pos] = buf;

    return rc;
}
