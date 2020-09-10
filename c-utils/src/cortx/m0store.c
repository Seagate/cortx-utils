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


/* Open a motr entity.
 * @param[in] - A pointer to motr entity to be opened
 * @return    - 0 on success and on failure returns the same
 *              error code given by underlyig storage API
*/
static int open_entity(struct m0_entity *entity)
{
	int rc = 0;
	struct m0_op *ops[1] = {NULL};

	dassert(entity);

	RC_WRAP_LABEL(rc, out, m0_entity_open, entity, &ops[0]);
	dassert(ops[0] != NULL);

	m0_op_launch(ops, 1);

	RC_WRAP_LABEL(rc, out, m0_op_wait, ops[0],
		      M0_BITS(M0_OS_FAILED, M0_OS_STABLE),
		      M0_TIME_NEVER);

	RC_WRAP_LABEL(rc, out, m0_rc, ops[0]);

out:
	if (rc) {
		RC_WRAP_SET(rc);
	}

	if (ops[0]) {
		m0_op_fini(ops[0]);
		m0_op_free(ops[0]);
	}
	return rc;
}

static void m0_indexvec_fill_extents(struct m0_indexvec *extents,
				    m0_bindex_t off,
				    m0_bcount_t block_count,
				    m0_bcount_t block_size)
{
	m0_bcount_t i;

	for (i = 0; i < block_count; i++) {
		extents->iv_index[i] = off;
		extents->iv_vec.v_count[i] = block_size;
		off += block_size;
	}
}

static int m0store_io_init(struct motr_io_ctx *ioctx, off_t off,
			   int block_count, int block_size)
{
	int	     rc;
	int	     i;
	/* Allocate block_count * 4K data buffer. */
	rc = m0_bufvec_alloc(&ioctx->data, block_count, block_size);
	if (rc != 0)
		goto out_err;

	/* Allocate bufvec and indexvec for write. */
	rc = m0_bufvec_alloc(&ioctx->attr, block_count, 1);
	if (rc != 0)
		goto out_free_data;

	rc = m0_indexvec_alloc(&ioctx->ext, block_count);
	if (rc != 0)
		goto out_free_attr;

	m0_indexvec_fill_extents(&ioctx->ext, off, block_count, block_size);

	for (i = 0; i < block_count; i++) {
		/* we don't want any attributes */
		ioctx->attr.ov_vec.v_count[i] = 0;
	}

	return 0;

out_free_attr:
	m0_bufvec_free(&ioctx->attr);
out_free_data:
	m0_bufvec_free(&ioctx->data);
out_err:
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

	if (!my_init_done)
		m0kvs_reinit();

	memset(&obj, 0, sizeof(struct m0_obj));

	m0_obj_init(&obj, &motr_uber_realm, &id,
		    m0_client_layout_id(motr_instance));

	RC_WRAP_LABEL(rc, out, m0_entity_create, NULL, &obj.ob_entity,
		      &ops[0]);
	dassert(ops[0] != NULL);

	m0_op_launch(ops, ARRAY_SIZE(ops));

	RC_WRAP_LABEL(rc, cleanup, m0_op_wait, ops[0],
		      M0_BITS(M0_OS_FAILED, M0_OS_STABLE),
		      M0_TIME_NEVER);

	RC_WRAP_LABEL(rc, cleanup, m0_rc, ops[0]);

cleanup:
	if (ops[0]) {
		m0_op_fini(ops[0]);
		m0_op_free(ops[0]);
		m0_entity_fini(&obj.ob_entity);
	}

out:
	log_debug("fid = "U128X_F" rc=%d", U128_P(&id), rc);
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

	if (!my_init_done)
		m0kvs_reinit();

	memset(&obj, 0, sizeof(struct m0_obj));

	m0_obj_init(&obj, &motr_uber_realm, &id,
		    m0_client_layout_id(motr_instance));

	RC_WRAP_LABEL(rc, out, open_entity, &obj.ob_entity);

	RC_WRAP_LABEL(rc, out, m0_entity_delete, &obj.ob_entity,
		      &ops[0]);
	dassert(ops[0] != NULL);

	m0_op_launch(ops, ARRAY_SIZE(ops));

	RC_WRAP_LABEL(rc, out, m0_op_wait, ops[0],
		      M0_BITS(M0_OS_FAILED, M0_OS_STABLE),
		      M0_TIME_NEVER);

	RC_WRAP_LABEL(rc, out, m0_rc, ops[0]);

out:
	if (ops[0]) {
		m0_op_fini(ops[0]);
		m0_op_free(ops[0]);
		m0_entity_fini(&obj.ob_entity);
	}

	log_debug("fid = "U128X_F" rc=%d", U128_P(&id), rc);
	return rc;
}

int m0_ufid_get(struct m0_uint128 *ufid)
{
	int		  rc;

	rc = m0_ufid_next(&ufid_generator, 1, ufid);
	if (rc != 0) {
		log_err("Failed to generate a ufid: %d\n", rc);
		return rc;
	}

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

static int m0store_write_aligned(struct m0_uint128 id, char *buff, off_t off,
				int block_count, int block_size)
{
	int		  rc;
	int		  op_rc;
	int		  i;
	int		  nr_tries = 10;
	struct m0_obj obj;
	struct m0_op *ops[1] = {NULL};
	struct motr_io_ctx    ioctx;
	const uint64_t empty_mask = 0;
	const uint64_t empty_flag = 0;

	if (!my_init_done)
		m0kvs_reinit();

again:
	m0store_io_init(&ioctx, off, block_count, block_size);

	for (i = 0; i < block_count; i++)
		memcpy(ioctx.data.ov_buf[i],
		       (char *)(buff+i*block_size),
		       block_size);

	/* Set the  bject entity we want to write */
	memset(&obj, 0, sizeof(struct m0_obj));

	m0_obj_init(&obj, &motr_uber_realm, &id,
		    m0_client_layout_id(motr_instance));

	open_entity(&obj.ob_entity);

	/* Create the write request */
	m0_obj_op(&obj, M0_OC_WRITE,
		  &ioctx.ext, &ioctx.data, &ioctx.attr,
	          empty_mask, empty_flag, &ops[0]);

	/* Launch the write request*/
	m0_op_launch(ops, 1);

	/* wait */
	rc = m0_op_wait(ops[0],
			M0_BITS(M0_OS_FAILED,
			M0_OS_STABLE),
			M0_TIME_NEVER);
	op_rc = ops[0]->op_sm.sm_rc;

	/* fini and release */
	m0_op_fini(ops[0]);
	m0_op_free(ops[0]);
	m0_entity_fini(&obj.ob_entity);

	if (op_rc == -EINVAL && nr_tries != 0) {
		nr_tries--;
		ops[0] = NULL;
		sleep(5);
		goto again;
	}

	/* Free bufvec's and indexvec's */
	m0_indexvec_free(&ioctx.ext);
	m0_bufvec_free(&ioctx.data);
	m0_bufvec_free(&ioctx.attr);

	/*
	 *    /!\    /!\    /!\    /!\
	 *
	 * As far as I have understood, MOTR does the IO in full
	 * or does nothing at all, so returned size is aligned sized */
	return (block_count*block_size);
}

/*
 * TODO: Following code either needs to be cleaned up by clubbing up input
 *       params, returned code from motr APIs needs to be handled properly
 *       This API can be generalised to be re used for read and write operation
 *       or can be re written which should ensure mentioned points can get
 *       addressed
*/
static int m0store_prepare_for_read(struct m0_uint128 id,
				    char *buff, off_t off,
				    int block_count, int block_size,
				    int *error)
{
	int		     i;
	int		     rc;
	struct m0_op    *ops[1] = {NULL};
	struct m0_obj    obj;
	uint64_t		last_index;
	struct motr_io_ctx ioctx;
	const uint64_t empty_mask = 0;
	const uint64_t empty_flag = 0;

	if (!my_init_done)
		m0kvs_reinit();

	rc = m0_indexvec_alloc(&ioctx.ext, block_count);
	if (rc != 0)
		return rc;

	rc = m0_bufvec_alloc(&ioctx.data, block_count, block_size);
	if (rc != 0)
		return rc;
	rc = m0_bufvec_alloc(&ioctx.attr, block_count, 1);
	if (rc != 0)
		return rc;

	last_index = off;
	for (i = 0; i < block_count; i++) {
		ioctx.ext.iv_index[i] = last_index;
		ioctx.ext.iv_vec.v_count[i] = block_size;
		last_index += block_size;

		ioctx.attr.ov_vec.v_count[i] = 0;
	}

	/* Read the requisite number of blocks from the entity */
	memset(&obj, 0, sizeof(struct m0_obj));

	m0_obj_init(&obj, &motr_uber_realm, &id,
		    m0_client_layout_id(motr_instance));

	open_entity(&obj.ob_entity);

	/* Create the read request */
	rc = m0_obj_op(&obj, M0_OC_READ,
		       &ioctx.ext, &ioctx.data, &ioctx.attr,
		       empty_mask, empty_flag, &ops[0]);
	assert(rc == 0);
	assert(ops[0] != NULL);
	assert(ops[0]->op_sm.sm_rc == 0);

	m0_op_launch(ops, 1);

	/* wait */
	rc = m0_op_wait(ops[0],
			M0_BITS(M0_OS_FAILED,
			M0_OS_STABLE),
			M0_TIME_NEVER);
	assert(rc == 0);
	assert(ops[0]->op_sm.sm_state == M0_OS_STABLE);
	assert(ops[0]->op_sm.sm_rc == 0);

	rc = m0_rc(ops[0]);
	*error = rc;

	for (i = 0; i < block_count; i++)
		memcpy((char *)(buff + block_size*i),
		       (char *)ioctx.data.ov_buf[i],
		       ioctx.data.ov_vec.v_count[i]);


	/* fini and release */
	m0_op_fini(ops[0]);
	m0_op_free(ops[0]);
	m0_entity_fini(&obj.ob_entity);

	m0_indexvec_free(&ioctx.ext);
	m0_bufvec_free(&ioctx.data);
	m0_bufvec_free(&ioctx.attr);

	/*
	 *    /!\    /!\    /!\    /!\
	 *
	 * As far as I have understood, MOTR does the IO in full
	 * or does nothing at all, so returned size is aligned sized */
	return (block_count*block_size);
}

static int m0store_read_aligned(struct m0_uint128 id,
				 char *buff, off_t off,
				 int block_count, int block_size)
{
	int read_bytes;
	int error = 0;

	read_bytes = m0store_prepare_for_read(id, buff, off,
					      block_count, block_size,
					      &error);

	if ((error == -ENOENT) && (block_count > 1)) {
		/*
		 * Motr is not able to handle the case where some part of object
		 * have not been written or created. For that it returns -ENOENT
		 * and zeroed out the data for all the read block even though
		 * some of them are available and we should get valid data for
		 * them atleast. For such case, this is the workaround where
		 * if we are reading more than one block size we will read
		 * all the block one by one so that for originally available
		 * block we will get proper data.
		*/

		int i;
		for (i = 0; i < block_count; i++) {
			m0store_prepare_for_read(id,
						 buff + (i*block_size),
						 off + (i*block_size),
						 1,
						 block_size,
						 &error);
		}
	}
	return read_bytes;
}

/*
 * The following functions makes random IO by blocks
 *
 */

/*
 * Those two functions compute the Upper and Lower limits
 * for the block that contains the absolution offset <x>
 * For related variables will be named Lx and Ux in the code
 *
 * ----|-----------x-------|-----
 *     Lx		  Ux
 *
 * Note: Lx and Ux are multiples of the block size
 * @todo: Move to generic utils header
 */
static off_t lower(off_t x, size_t bs)
{
	return (x/bs)*bs;
}

/* 
 * @todo: Move to generic utils header
 */
static off_t upper(off_t x, size_t bs)
{
	return ((x/bs)+1)*bs;
}

/* equivalent of pwrite, but does only IO on full blocks */
ssize_t m0store_do_io(struct m0_uint128 id, enum io_type iotype,
		      off_t x, size_t len, size_t bs, char *buff)
{
	off_t Lx1, Lx2, Ux1, Ux2;
	off_t Lio, Uio, Ubond, Lbond;
	bool bprev, bnext, insider;
	off_t x1, x2;
	int bcount = 0;
	int rc;
	int delta_pos = 0;
	int delta_tmp = 0;
	ssize_t done = 0;
	char *tmpbuff;

	tmpbuff = malloc(bs);
	if (tmpbuff == NULL)
		return -ENOMEM;

	/*
	 * IO will not be considered the usual offset+len way
	 * but as segment starting from x1 to x2
	 */
	x1 = x;
	x2 = x+len;

	/* Compute Lower and Upper Limits for IO */
	Lx1 = lower(x1, bs);
	Lx2 = lower(x2, bs);
	Ux1 = upper(x1, bs);
	Ux2 = upper(x2, bs);

	/* Those flags preserve state related to the way
	 * the IO should be done.
	 * - insider is true : x1 and x2 belong to the
	 *   same block (the IO is fully inside a single block)
	 * - bprev is true : x1 is not a block limit
	 * - bnext is true : x2 is not a block limit
	 */
	bprev = false;
	bnext = false;
	insider = false;

	/* If not an "insider case", the IO can be made in 3 steps
	 * a) inside [x1,x2], find a set of contiguous aligned blocks
	 *    and do the IO on them
	 * b) if x1 is not aligned on block size, do a small IO on the
	 *    block just before the "aligned blocks"
	 * c) if x2 is not aligned in block size, do a small IO on the
	 *    block just after the "aligned blocks"
	 *
	 * Example: x1 and x2 are located so
	 *	   x <--------------- len ------------------>
	 *  ---|-----x1-----|------------|------------|-------x2--|----
	 *     Lx1	  Ux1		       Lx2	 Ux2
	 *
	 * We should (write case)
	 *   1) read block [Lx1, Ux1] and update range [x1, Ux1]
	 *     then write updated [Lx1, Ux1]
	 *   3) read block [Lx2, Ux2], update [Lx2, x2] and
	 *       then writes back updated [Lx2, Ux2]
	 */
#if 0
	printf("IO: (%lld, %llu) = [%lld, %lld]\n",
		(long long)x, (unsigned long long)len,
		(long long)x1, (long long)x2);

	printf("  Bornes: %lld < %lld < %lld ||| %lld < %lld < %lld\n",
		(long long)Lx1, (long long)x1, (long long)Ux1,
		(long long)Lx2, (long long)x2, (long long)Ux2);
#endif
	/* In the following code, the variables of interest are:
	 *  - Lio and Uio are block aligned offset that limit
	 *    the "aligned blocks IO"
	 *  - Ubond and Lbound are the Up and Low limit for the
	 *    full IO, showing every block that was touched. It is
	 *    used for debug purpose */
	if ((Lx1 == Lx2) && (Ux1 ==  Ux2)) {
		/* Insider case, x1 and x2 are so :
		 *  ---|-x1---x2----|---
		 */
		bprev = bnext = false;

		insider = true;
		Lio = Uio = 0LL;
		Ubond = Ux1;
		Lbond = Lx1;
	} else {
		/* Left side */
		if (x1 == Lx1) {
			/* Aligned on the left
			* --|------------|----
			*   x1
			*   Lio
			*   Lbond
			*/
			Lio = x1;
			bprev = false;
			Lbond = x1;
		} else {
			/* Not aligned on the left
			* --|-----x1------|----
			*		 Lio
			*   Lbond
			*/
			Lio = Ux1;
			bprev = true;
			Lbond = Lx1;
		}

		/* Right side */
		if (x2 == Lx2) {
			/* Aligned on the right
			* --|------------|----
			*		x2
			*		Uio
			*		Ubond
			*/
			Uio = x2;
			bnext = false;
			Ubond = x2;
		} else {
			/* Not aligned on the left
			* --|---------x2--|----
			*   Uio
			*		 Ubond
			*/
			Uio = Lx2;
			bnext = true;
			Ubond = Ux2;
		}
	}

	/* delta_pos is the offset position in input buffer "buff"
	 * What is before buff+delta_pos has already been done */
	delta_pos = 0;
	if (bprev) {
		/* Reads block [Lx1, Ux1] before aligned [Lio, Uio] */
		memset(tmpbuff, 0, bs);
		rc = m0store_read_aligned(id, tmpbuff, Lx1, 1, bs);
		if (rc < 0 || rc != bs) {
			free(tmpbuff);
			return -1;
		}

		/* Update content of read block
		 * --|-----------------------x1-----------|---
		 *   Lx1				  Ux1
		 *			      WORK HERE
		 *    <----------------------><---------->
		 *	  x1-Lx1		Ux1-x1
		 */
		delta_tmp = x1 - Lx1;
		switch (iotype) {
		case IO_WRITE:
			memcpy((char *)(tmpbuff+delta_tmp),
			       buff, (Ux1 - x1));

			/* Writes block [Lx1, Ux1] once updated */
			rc = m0store_write_aligned(id, tmpbuff, Lx1, 1, bs);
			if (rc < 0 || rc != bs) {
				free(tmpbuff);
				return -1;
			}

			break;

		case IO_READ:
			 memcpy(buff, (char *)(tmpbuff+delta_tmp),
			       (Ux1 - x1));
			break;

		default:
			free(tmpbuff);
			return -EINVAL;
		}

		delta_pos += Ux1 - x1;
		done += Ux1 - x1;
	}

	if (Lio != Uio) {
		/* Easy case: aligned IO on aligned limit [Lio, Uio] */
		/* If no aligned block were found, then Uio == Lio */
		bcount = (Uio - Lio)/bs;
		switch (iotype) {
		case IO_WRITE:
			rc = m0store_write_aligned(id, (char *)(buff + delta_pos),
						Lio, bcount, bs);

			if (rc < 0) {
				free(tmpbuff);
				return -1;
			}
			break;

		case IO_READ:
			rc = m0store_read_aligned(id, (char *)(buff + delta_pos),
					       Lio, bcount, bs);

			if (rc < 0) {
				free(tmpbuff);
				return -1;
			}
			break;

		default:
			free(tmpbuff);
			return -EINVAL;
		}

		if (rc != (bcount*bs)) {
			free(tmpbuff);
			return -1;
		}

		done += rc;
		delta_pos += done;
	}

	if (bnext) {
		/* Reads block [Lx2, Ux2] after aligned [Lio, Uio] */
		memset(tmpbuff, 0, bs);
		rc = m0store_read_aligned(id, tmpbuff, Lx2, 1, bs);
		if (rc < 0) {
			free(tmpbuff);
			return -1;
		}

		/* Update content of read block
		 * --|---------------x2------------------|---
		 *   Lx2				 Ux2
		 *       WORK HERE
		 *    <--------------><------------------>
		 *	  x2-Lx2	   Ux2-x2
		 */
		switch (iotype) {
		case IO_WRITE:
			memcpy(tmpbuff, (char *)(buff + delta_pos),
			      (x2 - Lx2));

			/* Writes block [Lx2, Ux2] once updated */
			/* /!\ This writes extraenous ending zeros */
			rc = m0store_write_aligned(id, tmpbuff, Lx2, 1, bs);
			if (rc < 0) {
				free(tmpbuff);
				return -1;
			}
			break;

		case IO_READ:
			memcpy((char *)(buff + delta_pos), tmpbuff,
			       (x2 - Lx2));
			break;

		default:
			free(tmpbuff);
			return -EINVAL;
		}

		done += x2 - Lx2;
	}

	if (insider) {
		/* Insider case read/update/write */
		memset(tmpbuff, 0, bs);
		rc = m0store_read_aligned(id, tmpbuff, Lx1, 1, bs);
		if (rc < 0) {
			free(tmpbuff);
			return -1;
		}

		/* --|----------x1---------x2------------|---
		 *   Lx1=Lx2			     Ux1=Ux2
		 *		  UPDATE
		 *    <---------><---------->
		 *       x1-Lx1      x2-x1
		 */
		delta_tmp = x1 - Lx1;
		switch (iotype) {
		case IO_WRITE:
			memcpy((char *)(tmpbuff+delta_tmp), buff,
			       (x2 - x1));

			/* /!\ This writes extraenous ending zeros */
			rc = m0store_write_aligned(id, tmpbuff, Lx1, 1, bs);
			if (rc < 0) {
				free(tmpbuff);
				return -1;
			}
			break;

		case IO_READ:
			memcpy(buff, (char *)(tmpbuff+delta_tmp),
			       (x2 - x1));
			break;

		default:
			free(tmpbuff);
			return -EINVAL;
		}

		done += x2 - x1;
	}
#if 0
	printf("Complete IO : [%lld, %lld] => [%lld, %lld]\n",
		(long long)x1, (long long)x2,
		(long long)Lbond, (long long)Ubond);

	printf("End of IO : len=%llu  done=%lld\n\n",
	       (long long)len, (long long)done);
#endif
	free(tmpbuff);
	return done;
}

/** Synchronously deallocates the given vector of extents. */
static int m0_file_unmap_extents(const struct m0_uint128 *fid,
				 struct m0_indexvec *extents)
{
	int rc;
	int op_rc;
	struct m0_obj obj;
	struct m0_op *ops[1] = {NULL};
	const uint64_t empty_mask = 0;
	const uint64_t empty_flag = 0;

	if (!my_init_done)
		m0kvs_reinit();

	M0_SET0(&obj);
	m0_obj_init(&obj, &motr_uber_realm, fid,
		    m0_client_layout_id(motr_instance));

	/* Put entity in open state */
	open_entity(&obj.ob_entity);
	assert(obj.ob_entity.en_sm.sm_state == M0_ES_OPEN);

	/* Create an UMMAP request */
	m0_obj_op(&obj, M0_OC_FREE,
		  extents, NULL, NULL, empty_mask, empty_flag, &ops[0]);

	/* Launch the request*/
	m0_op_launch(ops, 1);

	/* Wait for completion */
	rc = m0_op_wait(ops[0],
			M0_BITS(M0_OS_FAILED,
			M0_OS_STABLE),
			M0_TIME_NEVER);
	op_rc = ops[0]->op_sm.sm_rc;

	/* Finalize operation */
	m0_op_fini(ops[0]);
	m0_op_free(ops[0]);
	/* Close entity */
	m0_entity_fini(&obj.ob_entity);

	if (rc != 0) {
		log_err("Failed to wait for operation "
			" completion (%d).\n", rc);
	} else if (op_rc != 0) {
		log_err("Trunc operation has failed (%d).\n", rc);
		rc = op_rc;
	}

	return rc;
}

/** Syncronously writes zeros into the given region of an object. */
static int m0_file_zero(const struct m0_uint128 *fid,
			m0_bcount_t count,
			m0_bindex_t offset,
			m0_bcount_t bsize)
{
	void *buf = NULL;
	int rc;

	buf = calloc(1, count);
	if (buf == NULL) {
		rc = -ENOMEM;
		goto out;
	}

	rc = m0store_do_io(*fid, IO_WRITE, offset, count, bsize, buf);
	free(buf);

	if (rc == count) {
		/* do not return positive int in case of success */
		rc = 0;
	}

out:
	return rc;
}

/* NSAL_TUNEABLE:
 * Size of data block that can be definitely UNMAP-ed by Motr
 * without generating errors at RPC layer or getting stuck somewhere
 * in the state machine.
 */
/* Default value: 5120 4K pages or 20 1MB pages or 20MB of data */
static const uint64_t m0_cortxfs_trunc_data_per_request = 20 * (1 << 20);

/** Submits UNMAP requests to Clvois and waits until the data blocks
 * are actually unmapped.
 * NOTE: Motr is not able to handle large extents in the truncate operations,
 * so that we are sending only small portions of extents per request.
 */
static int m0store_unmap_aligned(struct m0_uint128 fid,
			         size_t nblocks,
			         size_t offset,
			         size_t bsize)
{
	int rc;
	struct m0_indexvec extent;
	size_t nrequests = 0;
	size_t nblk_per_req = 0;
	size_t ndata_per_req = 0;
	size_t tail_size = 0;
	size_t i;

	M0_DASSERT(bsize != 0);
	M0_DASSERT(bsize % 2 == 0);
	M0_DASSERT(offset % bsize == 0);
	/* offset + nblocks * bsize == count, count <= SIZE_MAX */
	M0_DASSERT(SIZE_MAX / bsize >= (offset / bsize) + nblocks);

	if (nblocks == 0) {
		log_info("Nothing to unmap.\n");
		goto out;
	}

	ndata_per_req = lower(m0_cortxfs_trunc_data_per_request, bsize);
	nblk_per_req = ndata_per_req / bsize;
	nrequests = nblocks / nblk_per_req;
	tail_size = (nblocks * bsize) - (nrequests * ndata_per_req);

	M0_DASSERT(ergo(nblocks * bsize - offset < ndata_per_req,
			   nrequests == 0));

	rc = m0_indexvec_alloc(&extent, 1);
	if (rc != 0) {
		goto out;
	}

	/* Synchonously deallocate a batch of extents (ndata_per_req in each
	 * extent) and then synchronously deallocate the tail
	 * which is not aligned with the ndata_per_req value.
	 */

	for (i = 0; i < nrequests; i++) {
		log_info("De-allocating large extent[%d]: off=%llu, size=%d, "
			  "done=%.02f%%\n",
			  (int) i,
			  (unsigned long long) offset,
			  (int) ndata_per_req,
			  (((float) i * ndata_per_req) / (nblocks * bsize)) * 100);

		extent.iv_index[0] = offset;
		extent.iv_vec.v_count[0] = ndata_per_req;

		rc = m0_file_unmap_extents(&fid, &extent);
		if (rc != 0) {
			log_err("Failed to unmap the extent: %llu, %llu.\n",
				(unsigned long long) offset,
				(unsigned long long) ndata_per_req);
			goto out_free_extent;
		}

		offset += ndata_per_req;
	}

	if (tail_size) {
		log_info("De-allocating tail extent: off=%llu, size=%d\n",
			  (unsigned long long) offset,
			  (int) tail_size);
		extent.iv_index[0] = offset;
		extent.iv_vec.v_count[0] = tail_size;
		rc = m0_file_unmap_extents(&fid, &extent);
		if (rc != 0) {
			goto out_free_extent;
		}
	}

out_free_extent:
	m0_indexvec_free(&extent);
out:
	return rc;
}

int m0_file_unmap(struct m0_uint128 fid, size_t count, off_t offset)
{
	int rc;
	int bsize; /* Motr block size */
	size_t nblocks; /* n blocks to be deallocated */
	size_t aligned_off; /* Rounded up offset */

	bsize = m0store_get_bsize(fid);

	M0_DASSERT(bsize > 0);
	M0_DASSERT(bsize % 2 == 0);

	/* FIXME:EOS-1819: should we support count/offset  more than 7EB? */
	M0_DASSERT(count < INT64_MAX);
	M0_DASSERT(offset < INT64_MAX);
	M0_DASSERT(count != 0);

	/* adjust to the very first byte of the nearest (from right) page */
	aligned_off = m0_round_up(offset, bsize);
	/* cut out the left unaligned part from the whole len,
	 * round it up and then count the amount of blocks */
	nblocks = m0_round_up((count + offset) - aligned_off, bsize) / bsize;

	/* A special case where the caller wants to free a small range
	 * which cannot be de-allocated.
	 */
	if (m0_round_up(offset, bsize) == m0_round_up(offset + count, bsize)) {
		log_info("the range [%llu,%llu] is inside a single block %llu\n",
			  (unsigned long long) offset,
			  (unsigned long long) offset + count,
			  (unsigned long long) aligned_off);
		/* FIXME:EOS-1819: We should write zeros here because if
		 * the client would like to increase the file size back,
		 * the extented space must be read as zeros. */
		rc = m0_file_zero(&fid, count, offset, bsize);
		/* no need to do actual UNMAP */
		goto out;
	}

	/* A special case where the left edge is not aligned with the block
	 * size. The unaligned space must be zeroed.
	 */
	if (offset != aligned_off) {
		M0_DASSERT(offset < aligned_off);
		log_info("Non-freed range=[%llu, %llu]\n",
			  (unsigned long long) offset,
			  (unsigned long long) aligned_off);
		/* FIXME: the same case: zero the range which won't be unmapped */
		rc = m0_file_zero(&fid, aligned_off - offset, offset, bsize);
		if (rc != 0) {
			goto out;
		}
		/* now unmap the aligned pages */
	}

	rc = m0store_unmap_aligned(fid, nblocks, aligned_off, bsize);

out:
	return rc;
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

	dassert(id);
	dassert(pobj);

	fid = M0_UINT128(id->f_hi, id->f_lo);

	M0_SET0(pobj);

	m0_obj_init(pobj, &motr_uber_realm, &fid,
		    m0_client_layout_id(motr_instance));

	rc = m0_entity_open(&pobj->ob_entity, &op);
	if (rc) {
		RC_WRAP_SET(rc);
		goto out;
	}

	m0_op_launch(&op, 1);
	rc = m0_op_wait(op, M0_BITS(M0_OS_FAILED,
			M0_OS_STABLE),
			M0_TIME_NEVER);
	if (rc) {
		RC_WRAP_SET(rc);
		goto out;
	}

	rc = m0_rc(op);
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
	return rc;
}

void m0store_obj_close(struct m0_obj *obj)
{
	dassert(obj);

	log_debug("close (%p, " U128X_F ")", obj,
		  U128_P(&obj->ob_entity.en_id));
	m0_entity_fini(&obj->ob_entity);
}

/*****************************************************************************/
