/*
 * Filename:         m0common.h
 * Description:      Contains declarations needed by m0kvs.c & m0store.c

 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.

 Contains declarations needed by m0kvs.c & m0store.c
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

#include "clovis/clovis.h"
#include "clovis/clovis_internal.h"
#include "clovis/clovis_idx.h"
#include "lib/thread.h"
#include <eos/helpers.h>
#include <mero/helpers/helpers.h>

struct clovis_io_ctx {
	struct m0_indexvec ext;
	struct m0_bufvec   data;
	struct m0_bufvec   attr;
};

enum {
	 KVS_FID_STR_LEN = 128
};

/* To be passed as argument */
extern struct m0_clovis_realm     clovis_uber_realm;

extern pthread_once_t clovis_init_once;
extern bool clovis_init_done;
extern __thread struct m0_thread m0thread;
extern __thread bool my_init_done;

extern pthread_t m0init_thread;
extern struct collection_item *conf;

extern struct m0_fid ifid;
extern struct m0_clovis_idx idx;

extern char *clovis_local_addr;
extern char *clovis_ha_addr;
extern char *clovis_prof;
extern char *clovis_proc_fid;
extern char *clovis_index_dir;
extern char *ifid_str;

/* Clovis Instance */
extern struct m0_clovis	  *clovis_instance;

/* Clovis container */
extern struct m0_clovis_container clovis_container;

/* Clovis Configuration */
extern struct m0_clovis_config	clovis_conf;
extern struct m0_idx_dix_config	dix_conf;

extern struct m0_clovis_realm     clovis_uber_realm;

extern struct m0_ufid_generator ufid_generator;

#define WRAP_CONFIG(__name, __cfg, __item) ({\
	int __rc = get_config_item("mero", __name, __cfg, &__item);\
	if (__rc != 0)\
		return -__rc;\
	if (__item == NULL)\
		return -EINVAL; })

void m0kvs_do_init(void);
int get_clovis_conf(struct collection_item *cfg);
void log_config(void);
int init_clovis(void);

#endif
