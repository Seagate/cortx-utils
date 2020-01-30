/*
 * Filename:         m0kvs.c
 * Description:      Contains mero related kv operations

 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.

 Contains mero related kv operations which use clovis index.
*/

#include "m0common.h"
#include "common/log.h"
#include <debug.h>

int m0kvs_reinit(void)
{
	return m0init(conf);
}

void m0kvs_do_init(void)
{
	int rc;

	rc = get_clovis_conf(conf);

	if (rc != 0) {
		log_err("Invalid config file\n");
		exit(1);
	}

	log_config();

	rc = init_clovis();
	assert(rc == 0);

	clovis_init_done = true;
	m0init_thread = pthread_self();
}


static int m0_op_kvs(enum m0_clovis_idx_opcode opcode,
		     struct m0_bufvec *key,
		     struct m0_bufvec *val)
{
	struct m0_clovis_op	 *op = NULL;
	int rcs[1];
	int rc;

	if (!my_init_done)
		m0kvs_reinit();

	rc = m0_clovis_idx_op(&idx, opcode, key, val,
			      rcs, M0_OIF_OVERWRITE, &op);
	if (rc)
		return rc;

	m0_clovis_op_launch(&op, 1);
	rc = m0_clovis_op_wait(op, M0_BITS(M0_CLOVIS_OS_STABLE),
			       M0_TIME_NEVER);
	if (rc)
		goto out;

	/* Check rcs array even if op is succesful */
	rc = rcs[0];

out:
	m0_clovis_op_fini(op);
	/* it seems like 0_free(&op) is not needed */
	return rc;
}

int m0idx_create(const struct m0_uint128 *fid, struct m0_clovis_idx **index)
{
        int                     rc;
	struct m0_clovis_op    *op = NULL;
	struct m0_clovis_idx   *idx = NULL;

	*index = NULL;

	idx = m0kvs_alloc(sizeof(struct m0_clovis_idx));
	if (idx == NULL) {
		rc = -ENOMEM;
		goto out;
	}

	/* Set an index creation operation. */
	m0_clovis_idx_init(idx,
			&clovis_container.co_realm, (struct m0_uint128 *)fid);

        rc = m0_clovis_entity_create(NULL, &(idx->in_entity), &op);
	if (rc == 0) {
 		/* Launch and wait for op to complete */
        	m0_clovis_op_launch(&op, 1);
        	rc = m0_clovis_op_wait(op,
        		M0_BITS(M0_CLOVIS_OS_FAILED,
                	M0_CLOVIS_OS_STABLE),
                	M0_TIME_NEVER);
		if (rc == 0) {
			rc = op->op_rc;
		}
	}

        /* fini and release */
        m0_clovis_op_fini(op);
        m0_clovis_op_free(op);

	if (rc) {
		m0kvs_free(idx);
	} else {
		*index = idx;
	}

out:
        return rc;
}

int m0idx_delete(const struct m0_uint128 *fid)
{
        int                     rc;
        struct m0_clovis_op     *op;
        struct m0_clovis_idx    idx;

        memset(&idx, 0, sizeof(struct m0_clovis_idx));

        /* Set an index creation operation. */
        m0_clovis_idx_init(&idx,
                &clovis_container.co_realm, (struct m0_uint128 *)fid);

	rc = m0_clovis_entity_open(&idx.in_entity, &op);
	if (rc != 0) {
		goto out;
	}

        rc = m0_clovis_entity_delete(&(idx.in_entity), &op);
	if (rc == 0) {
        	/* Launch and wait for op to complete */
        	m0_clovis_op_launch(&op, 1);
        	rc = m0_clovis_op_wait(op,
        		M0_BITS(M0_CLOVIS_OS_FAILED,
                	M0_CLOVIS_OS_STABLE),
                	M0_TIME_NEVER);
		if (rc == 0) {
        		rc = op->op_rc;
		}
	}

        /* fini and release */
        m0_clovis_op_fini(op);
        m0_clovis_op_free(op);

out:
        m0_clovis_entity_fini(&(idx.in_entity));
        return rc;
}

int m0idx_open(const struct m0_uint128 *fid, struct m0_clovis_idx **index)
{
	int 			rc = 0;
	struct m0_clovis_idx  	*idx = NULL;
	
	*index = NULL;

	idx = m0kvs_alloc(sizeof(struct m0_clovis_idx));
        if (idx == NULL) {
                rc = -ENOMEM;
		goto out;
        }

        m0_clovis_idx_init(idx, &clovis_container.co_realm,
                           (struct m0_uint128 *)fid);

	*index = idx;

out:
	return rc;
}

void m0idx_close(struct m0_clovis_idx *index)
{
        m0_clovis_idx_fini(index);
	m0kvs_free(index);
}

static int m0_op2_kvs(void *ctx,
		      enum m0_clovis_idx_opcode opcode,
		      struct m0_bufvec *key,
		      struct m0_bufvec *val)
{
	struct m0_clovis_op	 *op = NULL;
	int rcs[1];
	int rc;

	struct m0_clovis_idx     *index = NULL;

	if (!my_init_done)
		m0kvs_reinit();

	index = ctx;

	rc = m0_clovis_idx_op(index, opcode, key, val,
			      rcs, M0_OIF_OVERWRITE, &op);
	if (rc)
		return rc;

	m0_clovis_op_launch(&op, 1);
	rc = m0_clovis_op_wait(op, M0_BITS(M0_CLOVIS_OS_STABLE),
			       M0_TIME_NEVER);
	if (rc)
		goto out;

	/* Check rcs array even if op is succesful */
	rc = rcs[0];

out:
	m0_clovis_op_fini(op);
	/* it seems like 0_free(&op) is not needed */
	return rc;
}

int m0kvs_get(void *ctx, void *k, size_t klen,
	       void **v, size_t *vlen)
{
	m0_bcount_t k_len = klen;
	struct m0_bufvec key, val;
	int rc;

	// @todo: Assert is called when NFS Ganesha is run.
	// Once issue is debugged uncomment the M0_DASSERT call.
	if (!my_init_done)
		m0kvs_reinit();
	//M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(v, vlen);

	rc = m0_op2_kvs(ctx, M0_CLOVIS_IC_GET, &key, &val);
	if (rc != 0)
		goto out;

out:
	return rc;
}

int m0kvs4_get(void *k, size_t klen,
	       void **v, size_t *vlen)
{
	m0_bcount_t k_len = klen;
	struct m0_bufvec key, val;
	int rc;

	// @todo: Assert is called when NFS Ganesha is run.
	// Once issue is debugged uncomment the M0_DASSERT call.
	if (!my_init_done)
		m0kvs_reinit();
	//M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(v, vlen);

	rc = m0_op_kvs(M0_CLOVIS_IC_GET, &key, &val);
	if (rc != 0)
		goto out;

out:
	return rc;
}

int m0kvs4_set(void *k, const size_t klen,
	       void *v, const size_t vlen)
{
	m0_bcount_t k_len = klen;
	m0_bcount_t v_len = vlen;
	struct m0_bufvec key, val;
	int rc;

	M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(&v, &v_len);

	rc = m0_op_kvs(M0_CLOVIS_IC_PUT, &key, &val);
	return rc;
}

int m0kvs_set(void *ctx, void *k, const size_t klen,
	       void *v, const size_t vlen)
{
	m0_bcount_t k_len = klen;
	m0_bcount_t v_len = vlen;
	struct m0_bufvec key, val;
	int rc;

	M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);
	val = M0_BUFVEC_INIT_BUF(&v, &v_len);

	rc = m0_op2_kvs(ctx, M0_CLOVIS_IC_PUT, &key, &val);
	return rc;
}

int m0kvs_del(void *ctx, void *k, const size_t klen)
{
	struct m0_bufvec key;
	m0_bcount_t k_len = klen;
	int rc;

	M0_DASSERT(my_init_done);

	key = M0_BUFVEC_INIT_BUF(&k, &k_len);

	rc = m0_op2_kvs(ctx, M0_CLOVIS_IC_DEL, &key, NULL);
	return rc;
}

int m0kvs_list_set(void *ctx, struct m0kvs_list *key,
                   struct m0kvs_list *val)
{
	int rc;

	rc = m0_op2_kvs(ctx, M0_CLOVIS_IC_PUT, &key->buf, &val->buf);
	return rc;
}

int m0kvs_list_get(void *ctx, struct m0kvs_list *key,
                   struct m0kvs_list *val)
{
	int rc;

	rc = m0_op2_kvs(ctx, M0_CLOVIS_IC_GET, &key->buf, &val->buf);
	return rc;
}

int m0kvs_pattern(void *ctx, char *k, char *pattern,
		    get_list_cb cb, void *arg_cb)
{
	struct m0_bufvec          keys;
	struct m0_bufvec          vals;
	struct m0_clovis_op       *op = NULL;
	struct m0_clovis_idx      *index = ctx;
	int i = 0;
	int rc;
	int rcs[1];
	bool stop = false;
	char myk[KLEN];
	bool startp = false;
	int size = 0;
	int flags;

	strcpy(myk, k);
	flags = 0; /* Only for 1st iteration */

	do {
		/* Iterate over all records in the index. */
		rc = m0_bufvec_alloc(&keys, 1, KLEN);
		if (rc != 0)
			return rc;

		rc = m0_bufvec_alloc(&vals, 1, VLEN);
		if (rc != 0) {
			m0_bufvec_free(&keys);
			return rc;
		}

		/* FIXME: Memory leak? check m0_bufvec_alloc
		 * documentation. We don't need to allocate
		 * the buffer twice.
		 */
		keys.ov_buf[0] = m0_alloc(strnlen(myk, KLEN)+1);
		keys.ov_vec.v_count[0] = strnlen(myk, KLEN)+1;
		strcpy(keys.ov_buf[0], myk);

		rc = m0_clovis_idx_op(index, M0_CLOVIS_IC_NEXT, &keys, &vals,
				      rcs, flags, &op);
		if (rc != 0) {
			m0_bufvec_free(&keys);
			m0_bufvec_free(&vals);
			return rc;
		}
		m0_clovis_op_launch(&op, 1);
		rc = m0_clovis_op_wait(op, M0_BITS(M0_CLOVIS_OS_STABLE),
				       M0_TIME_NEVER);
		/* @todo : Why is op null after this call ??? */

		if (rc != 0) {
			m0_bufvec_free(&keys);
			m0_bufvec_free(&vals);
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

	return size;
}

int m0kvs_key_prefix_exists(void *ctx,
			    const void *kprefix, size_t klen,
			    bool *result)
{
	struct m0_bufvec keys;
	struct m0_bufvec vals;
	struct m0_clovis_op *op = NULL;
	struct m0_clovis_idx *index = ctx;
	int rc;
	int rcs[1];

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

	rc = m0_clovis_idx_op(index, M0_CLOVIS_IC_NEXT, &keys, &vals,
			      rcs, 0,  &op);

	if (rc != 0) {
		goto out_free_vals;
	}

	if (rcs[0] != 0) {
		goto out_free_vals;
	}

	m0_clovis_op_launch(&op, 1);
	rc = m0_clovis_op_wait(op, M0_BITS(M0_CLOVIS_OS_STABLE),
			       M0_TIME_NEVER);
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
		m0_clovis_op_fini(op);
		m0_clovis_op_free(op);
	}
out_free_vals:
	m0_bufvec_free(&vals);
out_free_keys:
	m0_bufvec_free(&keys);
out:
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
	if (!priv->initialized)
		goto out;

	m0_bufvec_free(&priv->key);
	m0_bufvec_free(&priv->val);

	if (priv->op) {
		m0_clovis_op_fini(priv->op);
		m0_clovis_op_free(priv->op);
	}
out:
	return;
}

int m0kvs_key_iter_find(const void* prefix, size_t prefix_len,
                        struct m0kvs_key_iter *priv)
{
	struct m0_bufvec *key = &priv->key;
	struct m0_bufvec *val = &priv->val;
	struct m0_clovis_op **op = &priv->op;
	struct m0_clovis_idx *index = priv->index;
	int rc;

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

	rc = m0_clovis_idx_op(index, M0_CLOVIS_IC_NEXT, &priv->key, &priv->val,
	                      priv->rcs, 0, op);

	if (rc != 0) {
		goto out_free_val;
	}

	m0_clovis_op_launch(op, 1);
	rc = m0_clovis_op_wait(*op, M0_BITS(M0_CLOVIS_OS_STABLE),
	                       M0_TIME_NEVER);

	if (rc != 0) {
		goto out_free_op;
	}

	if (priv->rcs[0] != 0) {
		goto out_free_op;
	}

	/* release objects back to priv */
	key = NULL;
	val = NULL;
	op = NULL;
	priv->initialized = true;

out_free_op:
	if (op && *op) {
		m0_clovis_op_fini(*op);
		m0_clovis_op_free(*op);
	}

out_free_val:
	if (val)
		m0_bufvec_free(val);
out_free_key:
	if (key)
		m0_bufvec_free(key);
out:
	if (rc != 0) {
		memset(&priv, 0, sizeof(*priv));
	}

	return rc;
}

int m0kvs_key_iter_next(struct m0kvs_key_iter *priv)
{
	struct m0_clovis_idx *index = priv->index;
	int rc = 0;

	dassert(priv->initialized);

	/* Clovis API: "'vals' vector ... should contain NULLs" */
	m0kvs_bufvec_free_data(&priv->val);

	rc = m0_clovis_idx_op(index, M0_CLOVIS_IC_NEXT,
	                      &priv->key, &priv->val, priv->rcs,
	                      M0_OIF_EXCLUDE_START_KEY,  &priv->op);
	if (rc != 0) {
		goto out;
	}

	m0_clovis_op_launch(&priv->op, 1);
	rc = m0_clovis_op_wait(priv->op, M0_BITS(M0_CLOVIS_OS_STABLE),
			       M0_TIME_NEVER);

	if (rc != 0) {
		goto out;
	}

	rc = priv->rcs[0];

out:
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
