/*
 * Filename:         m0common.h
 * Description:      Contains declarations needed by m0kvs.c & m0store.c
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

#ifndef _M0COMMON_H
#define _M0COMMON_H

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/time.h>
#include <sys/param.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <syscall.h> /* for gettid */
#include <fcntl.h>
#include <stdbool.h>
#include <errno.h>
#include <string.h>
#include <assert.h>
#include <pthread.h>
#include <dirent.h>

#include "motr/client.h"
#include "motr/client_internal.h"
#include "motr/idx.h"
#include "lib/thread.h"
#include <cortx/helpers.h>
#include <motr/helpers/helpers.h>

struct motr_io_ctx {
	struct m0_indexvec ext;
	struct m0_bufvec   data;
	struct m0_bufvec   attr;
};

enum {
	 KVS_FID_STR_LEN = 128
};

/* To be passed as argument */
extern struct m0_realm     motr_uber_realm;

extern pthread_once_t motr_init_once;
extern bool motr_init_done;
extern __thread struct m0_thread m0thread;
extern __thread bool my_init_done;

extern pthread_t m0init_thread;
extern struct collection_item *conf;

extern struct m0_fid ifid;
extern struct m0_idx idx;

extern char *motr_local_addr;
extern char *motr_ha_addr;
extern char *motr_prof;
extern char *motr_proc_fid;
extern char *motr_index_dir;
extern char *ifid_str;

/* Motr Instance */
extern struct m0_client	  *motr_instance;

/* Motr container */
extern struct m0_container motr_container;

/* Motr Configuration */
extern struct m0_config	motr_conf;
extern struct m0_idx_dix_config	dix_conf;

extern struct m0_realm     motr_uber_realm;

extern struct m0_ufid_generator ufid_generator;

#define WRAP_CONFIG(__name, __cfg, __item) ({\
	int __rc = get_config_item("motr", __name, __cfg, &__item);\
	if (__rc != 0)\
		return -__rc;\
	if (__item == NULL)\
		return -EINVAL; })

void m0kvs_do_init(void);
int get_motr_conf(struct collection_item *cfg);
void log_config(void);
int init_motr(void);

#endif
