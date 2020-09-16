/*
 * Filename:         helpers.h
 * Description:      Contains declarations of cortx functionality needed
 *                   by nsal, cortxfs, dsal
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

#ifndef _HELPERS_H
#define _HELPERS_H

#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <sys/time.h>
#include <assert.h>
#include <fnmatch.h>
#include <ini_config.h>
#include <utils.h>

#include "motr/client.h"
#include "motr/client_internal.h"
#include "motr/idx.h"

#include "object.h" /* obj_id_t */

#ifdef DEBUG
#define M0_DASSERT(cond) assert(cond)
#else
#define M0_DASSERT(cond)
#endif

#define KLEN (256)
#define VLEN (256)

struct m0kvs_list {
	struct m0_bufvec buf;
};

struct m0kvs_key_iter {
	struct m0_bufvec key;
	struct m0_bufvec val;
	struct m0_op *op;
	struct m0_idx *index;
	int rcs[1];
	bool initialized;
};

typedef bool (*get_list_cb)(char *k, void *arg);

int m0init(struct collection_item *cfg_items);
void m0fini(void);
int m0kvs_reinit(void);

int m0kvs_set(void *ctx, void *k, const size_t klen,
	       void *v, const size_t vlen);
int m0kvs4_set(void *k, const size_t klen,
	       void *v, const size_t vlen);
int m0kvs_get(void *ctx, void *k, size_t klen, void **v, size_t *vlen);
int m0kvs4_get(void *k, size_t klen, void **v, size_t *vlen);
int m0kvs_del(void *ctx, void *k, const size_t klen);
int m0kvs_idx_gen_fid(struct m0_uint128 *index_fid);
void m0_iter_kvs(char *k);
int m0kvs_pattern(void *ctx, char *k, char *pattern,
		  get_list_cb cb, void *arg_cb);
int m0kvs_key_prefix_exists(void *ctx, const void *kprefix, size_t klen,
			    bool *result);

/******************************************************************************/
/* Key Iterator */

/* TODO:PERF:
 *	Performance of key iterators can be improved by:
 *	1. Usage of prefetch.
 *	2. Async Motr calls.
 *	3. Piggyback data for records.
 *	The features can be implemented without significant changes in
 *	the caller code and mostly isolated in the m0common module.
 *
 *	1. The key prefetch feature requires an additional argument to specify
 *	the amount of records to retrieve in a NEXT motr call.
 *	Then, key_iter_next walks over the prefetched records and issues
 *	a NEXT call after the last portion of records was processed by the user.
 *
 *	2. The async motr calls feature can be used to speed up the case
 *	where the time of records processing by the caller is comparable with
 *	the time needed to receive next bunch of records from Motr.
 *	In this case a initial next call synchronously gets a bunch of records,
 *	and then immediately issues an asynchronous NEXT call.
 *	The consequent next call waits for the issued records,
 *	and again issues a NEXT call to motr. In conjunction with the prefetch
 *	feature, it can help to speed up readdir() by issuing NEXT (dentry)
 *	and GET (inode attrs) concurrently.
 *
 *	3. Since readdir requires a combination of NEXT + GET calls,
 *	the iterator can issue a GET call to get the inode attirbutes of
 *	prefetched dentries along with the next portion of NEXT dentries.
 *	So that, we can get a chunk of dentries and the attributes of the
 *	previous chunck witin a single motr call.
 *	However, this feature make sense only for the recent version of
 *	nfs-ganesha where a FSAL is resposible for filling in attrlist
 *	(the current version calls fsal_getattr() instead of it).
 */

/** Cleanup key iterator object */
void m0kvs_key_iter_fini(struct m0kvs_key_iter *priv);

/** Find the first record following by the prefix and set iter to it.
 * @param iter Iterator object to initialized with the starting record.
 * @param prefix Key prefix to be found.
 * @param prefix_len Length of the prefix.
 * @return True if found, otherwise False. @see kvstore_iter::inner_rc for
 * return code.
 */
int m0kvs_key_iter_find(const void* prefix, size_t prefix_len,
                        struct m0kvs_key_iter *priv);

/* Find the next record and set iter to it. */
int m0kvs_key_iter_next(struct m0kvs_key_iter *priv);

/**
 * Get pointer to key data.
 * @param[out] key View of key data owned by iter.
 * @param[out] klen Size of key.
 * @param[out] val View of value data owner by iter.
 * @param[out] vlen Size of value.
 */
void m0kvs_key_iter_get_kv(struct m0kvs_key_iter *priv, void **key,
                           size_t *klen, void **val, size_t *vlen);
int m0store_create_object(struct m0_uint128 id);
int m0store_delete_object(struct m0_uint128 id);
int m0_ufid_get(struct m0_uint128 *ufid);
int m0_fid_to_string(struct m0_uint128 *fid, char *fid_s);
void *m0kvs_alloc(uint64_t size);
void m0kvs_free(void *ptr);
int m0kvs_list_alloc(struct m0kvs_list *buf, uint32_t list_cnt);
void m0kvs_list_free(struct m0kvs_list *buf);
int m0kvs_list_set(void *ctx, struct m0kvs_list *key,
                   struct m0kvs_list *val);
int m0kvs_list_get(void *ctx, struct m0kvs_list *key,
                   struct m0kvs_list *val);
int m0kvs_list_add(struct m0kvs_list *kvs_buf, void *buf, size_t buf_len,
                   int index);

/*****************************************************************************/
/** Open a Motr object.
 * This function writes a new in-memory object into the provided "pobj"
 * storage, and it does not do any checks regarding the following topics:
 *	- (1) Existence of the object. Behavior of the function is the same as
 *	  behavior of the underlying storage. If it returns -ENOENT in some
 *	  cases then this function will also return -ENOENT in these cases.
 *	- (2) Overwriting of already open object. If "pobj" points to an object
 *	  that has already been open then the function will simply overwrite
 *	  this data.
 *	- Uniqueness of "pobj" contents. Two open objects may point to the
 *	  same storage object in the same way as two different FDs may
 *	  point to the same file.
 * Also, the function does not allocate storage for pobj (3) - it is up to
 * the caller to decide where it should be allocated.
 * These 4 points have been introduced deliberately here. The reason here
 * is that the upper layers (for example, DSAL) will be able to provide
 * "common" code for all its backends including this one.
 * This management (memory, existence, reopen) was not included in
 * the function in order to avoid code duplication.
 * @param[in] id FID of the object to be open.
 * @param[inout] pobj Pointer to pre-allocated storage for in-memory
 *		 representation of the object with the given FID.
 * @return 0 or -errno in case of failure.
 */
int m0store_obj_open(const obj_id_t *id, struct m0_obj *pobj);

/** Close a Motr object.
 * This function closes an open Motr object. It does not provide
 * any guarantees regarding the double-free problem. It is up
 * to the caller to guarantee the proper sequence of open/close calls.
 * An attempt to close an already closed object is UB.
 * It may either cause an m0_panic, SIGSEGV or it may do nothing.
 * @param[inout] obj Motr object that has been opened.
 */
void m0store_obj_close(struct m0_obj *obj);

/*****************************************************************************/

#define M0STORE_BLK_COUNT 10

enum io_type {
	IO_READ = 1,
	IO_WRITE = 2
};

#define CONF_STR_LEN 100

ssize_t m0store_get_bsize(struct m0_uint128 id);

static inline void m0_fid_copy(struct m0_uint128 *src, struct m0_uint128 *dest)
{
	dest->u_hi = src->u_hi;
	dest->u_lo = src->u_lo;
}

/** Creates a new index (a container for KVS records) in the underlying storage (Motr)
 * and returns a handle to be used in KVS operations within this index.
 * Note: The caller should release the resources associated with the handle
 * by calling m0idx_close.
 * @param fid In FID 
 * @param index Out on success a valid initialized motr index is returned.
 */
int m0idx_create(const struct m0_uint128 *fid, struct m0_idx **index);

/** Delete motr index instance.
 * @param fid In FID 
 * @param index Out on success a valid initialized motr index is returned.
 */
int m0idx_delete(const struct m0_uint128 *fid);

/** Initialize motr index instance.
 * @param fid In FID 
 * @param index Out on success a valid initialized motr index is returned.
 */
int m0idx_open(const struct m0_uint128 *fid, struct m0_idx **index);

/** Finalize motr index instance.
 * @param index Index to be finalized.
 */
void m0idx_close(struct m0_idx *index);

/* @todo FS mgmt work will revisit the need of this function */
const char * m0_get_gfid();

#endif
