/*
 * Filename:         m0common.c
 * Description:      Contains setup variables and functions of mero

 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.

 Contains all eos objects needed by m0kvs.c & m0store.c &
 implementation of init/fini APIs. 
*/

#include "m0common.h"
#include <common/log.h>

/* To be passed as argument */
struct m0_clovis_realm     clovis_uber_realm;

pthread_once_t clovis_init_once = PTHREAD_ONCE_INIT;
bool clovis_init_done = false;
__thread struct m0_thread m0thread;
__thread bool my_init_done = false;

pthread_t m0init_thread;
struct collection_item *conf = NULL;

struct m0_fid ifid;
struct m0_clovis_idx idx;

char *clovis_local_addr;
char *clovis_ha_addr;
char *clovis_prof;
char *clovis_proc_fid;
/* @todo: Fix hardcoded path */
char *clovis_index_dir = "/tmp/";
char *ifid_str;

/* Clovis Instance */
struct m0_clovis	  *clovis_instance = NULL;

/* Clovis container */
struct m0_clovis_container clovis_container;

/* Clovis Configuration */
struct m0_clovis_config	clovis_conf;
struct m0_idx_dix_config	dix_conf;

struct m0_clovis_realm     clovis_uber_realm;

struct m0_ufid_generator ufid_generator;

/* Non-static function starts here */
static pthread_mutex_t m0init_lock = PTHREAD_MUTEX_INITIALIZER;

const char * m0_get_gfid()
{
	return ifid_str;
}

int m0init(struct collection_item *cfg_items)
{
	if (cfg_items == NULL)
		return -EINVAL;

	if (conf == NULL)
		conf = cfg_items;

	(void) pthread_once(&clovis_init_once, m0kvs_do_init);

	pthread_mutex_lock(&m0init_lock);

	if (clovis_init_done && (pthread_self() != m0init_thread)) {
		log_info("==========> tid=%d I am not the init thread\n",
		       (int)syscall(SYS_gettid));

		memset(&m0thread, 0, sizeof(struct m0_thread));

		m0_thread_adopt(&m0thread, clovis_instance->m0c_mero);
	} else
		log_info("----------> tid=%d I am the init thread\n",
		       (int)syscall(SYS_gettid));

	pthread_mutex_unlock(&m0init_lock);

	my_init_done = true;

	return 0;
}

void m0fini(void)
{
	if (pthread_self() == m0init_thread) {
		/* Finalize Clovis instance */
		m0_clovis_idx_fini(&idx);
		m0_clovis_fini(clovis_instance, true);
	} else
		m0_thread_shun();
}

int get_clovis_conf(struct collection_item *cfg)
{
	struct collection_item *item;

	if (cfg == NULL)
		return -EINVAL;

	item = NULL;
	WRAP_CONFIG("local_addr", cfg, item);
	clovis_local_addr = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("ha_addr", cfg, item);
	clovis_ha_addr = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("profile", cfg, item);
	clovis_prof = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("proc_fid", cfg, item);
	clovis_proc_fid = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("index_dir", cfg, item);
	clovis_index_dir = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("kvs_fid", cfg, item);
	ifid_str = get_string_config_value(item, NULL);

	return 0;
}

void log_config(void)
{
	log_info("local_addr = %s\n", clovis_local_addr);
	log_info("ha_addr    = %s\n", clovis_ha_addr);
	log_info("profile    = %s\n", clovis_prof);
	log_info("proc_fid   = %s\n", clovis_proc_fid);
	log_info("index_dir  = %s\n", clovis_index_dir);
	log_info("kvs_fid    = %s\n", ifid_str);
	log_info("---------------------------\n");
}

int init_clovis(void)
{
	int rc;
	char  tmpfid[MAXNAMLEN];

	assert(clovis_local_addr && clovis_ha_addr && clovis_prof &&
	       clovis_proc_fid);

	/* Initialize Clovis configuration */
	clovis_conf.cc_is_oostore	= true;
	clovis_conf.cc_is_read_verify	= false;
	clovis_conf.cc_local_addr	= clovis_local_addr;
	clovis_conf.cc_ha_addr		= clovis_ha_addr;
	clovis_conf.cc_profile		= clovis_prof;
	clovis_conf.cc_process_fid       = clovis_proc_fid;
	clovis_conf.cc_tm_recv_queue_min_len    = M0_NET_TM_RECV_QUEUE_DEF_LEN;
	clovis_conf.cc_max_rpc_msg_size	 = M0_RPC_DEF_MAX_RPC_MSG_SIZE;
	clovis_conf.cc_layout_id	= 0;

	/* Index service parameters */
	clovis_conf.cc_idx_service_id	= M0_CLOVIS_IDX_DIX;
	dix_conf.kc_create_meta		= false;
	clovis_conf.cc_idx_service_conf	= &dix_conf;

	/* Create Clovis instance */
	rc = m0_clovis_init(&clovis_instance, &clovis_conf, true);
	if (rc != 0) {
		log_err("Failed to initilise Clovis\n");
		goto err_exit;
	}

	/* Container is where Entities (object) resides.
	 * Currently, this feature is not implemented in Clovis.
	 * We have only single realm: UBER REALM. In future with multiple realms
	 * multiple applications can run in different containers. */
	m0_clovis_container_init(&clovis_container,
				 NULL, &M0_CLOVIS_UBER_REALM,
				 clovis_instance);

	rc = clovis_container.co_realm.re_entity.en_sm.sm_rc;
	if (rc != 0) {
		log_err("Failed to open uber realm\n");
		goto err_exit;
	}

	clovis_uber_realm = clovis_container.co_realm;

	/* Get fid from config parameter */
	memset(&ifid, 0, sizeof(struct m0_fid));
	rc = m0_fid_sscanf(ifid_str, &ifid);
	if (rc != 0) {
		log_err("Failed to read ifid value from conf\n");
		goto err_exit;
	}

	rc = m0_fid_print(tmpfid, MAXNAMLEN, &ifid);
	if (rc < 0) {
		log_err("Failed to read ifid value from conf\n");
		goto err_exit;
	}

	m0_clovis_idx_init(&idx, &clovis_container.co_realm,
			   (struct m0_uint128 *)&ifid);

	rc = m0_ufid_init(clovis_instance, &ufid_generator);
	if (rc != 0) {
		log_err("Failed to initialise fid generator: %d\n", rc);
		goto err_exit;
	}

	return 0;

err_exit:
	return rc;
}
