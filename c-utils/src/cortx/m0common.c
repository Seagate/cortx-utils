/*
 * Filename:         m0common.c
 * Description:      Contains setup variables and functions of motr
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

/*
 * Contains all cortx objects needed by m0kvs.c & m0store.c &
 * implementation of init/fini APIs.
 */
 
#include "m0common.h"
#include <common/log.h>
#include <debug.h> /* dassert */
#include "perf/tsdb.h" /*  is_engine_on */

/* To be passed as argument */
struct m0_realm     motr_uber_realm;

pthread_once_t motr_init_once = PTHREAD_ONCE_INIT;
bool motr_init_done = false;
__thread struct m0_thread m0thread;
__thread bool my_init_done = false;

pthread_t m0init_thread;
struct collection_item *conf = NULL;

struct m0_fid ifid;
struct m0_idx idx;

char *motr_local_addr;
char *motr_ha_addr;
char *motr_prof;
char *motr_proc_fid;
/* @todo: Fix hardcoded path */
char *motr_index_dir = "/tmp/";
char *ifid_str;

/* Motr Instance */
struct m0_client	  *motr_instance = NULL;

/* Motr container */
struct m0_container motr_container;

/* Motr Configuration */
struct m0_config	motr_conf;
struct m0_idx_dix_config	dix_conf;

struct m0_realm     motr_uber_realm;

struct m0_ufid_generator ufid_generator;

/* Non-static function starts here */
static pthread_mutex_t m0init_lock = PTHREAD_MUTEX_INITIALIZER;

const char * m0_get_gfid()
{
	return ifid_str;
}

static pthread_key_t autoshun_key;
static pthread_once_t autoshun_key_init_once = PTHREAD_ONCE_INIT;

static void autoshun_key_cb(void *val)
{
	(void) val;
	if (m0_thread_tls()) {
		m0_thread_shun();
	}
}

static void autoshun_key_init(void)
{
	int rc;

	rc = -pthread_key_create(&autoshun_key, autoshun_key_cb);

	/* Assumption:
	 *	This function is always successful.
	 */
	assert(rc == 0);
}

static void autoshun_key_fini(void)
{
	pthread_key_delete(autoshun_key);
	memset(&autoshun_key, 0, sizeof(autoshun_key));
	autoshun_key_init_once = PTHREAD_ONCE_INIT;
}

void autoshun_key_register_thread(void)
{
	int rc;

	/* we do not care about the value stored there, we just
	 * need to make sure glibc put it in the array.
	 */
	const int dummy_value = 1;

	rc = pthread_setspecific(autoshun_key,
				 (const void *) (intptr_t) dummy_value);

	/* Assumption:
	 *	This function is always successful.
	 */
	assert(rc == 0);
}

int m0init(struct collection_item *cfg_items)
{
	if (cfg_items == NULL)
		return -EINVAL;

	if (conf == NULL)
		conf = cfg_items;

	/* Important note:
	 * The autoshun key should be registered before
	 * initializing M0. The autoshun-key hack relies on
	 * the internal representation of POSIX TLS in the glibc.
	 */
	(void) pthread_once(&autoshun_key_init_once, autoshun_key_init);
	(void) pthread_once(&motr_init_once, m0kvs_do_init);

	pthread_mutex_lock(&m0init_lock);

	if (motr_init_done && (pthread_self() != m0init_thread)) {
		log_info("==========> tid=%d I am not the init thread\n",
		       (int)syscall(SYS_gettid));

		memset(&m0thread, 0, sizeof(struct m0_thread));
		autoshun_key_register_thread();
		m0_thread_adopt(&m0thread, motr_instance->m0c_motr);
	} else
		log_info("----------> tid=%d I am the init thread\n",
		       (int)syscall(SYS_gettid));

	pthread_mutex_unlock(&m0init_lock);

	my_init_done = true;

	return 0;
}

void m0fini(void)
{
	/* We can finalize M0 only from a thread that has been adopted. */
	dassert(my_init_done);
	if (motr_instance) {
		m0_client_fini(motr_instance, true);
		motr_instance = NULL;
		autoshun_key_fini();
	}
}

int get_motr_conf(struct collection_item *cfg)
{
	struct collection_item *item;

	if (cfg == NULL)
		return -EINVAL;

	item = NULL;
	WRAP_CONFIG("local_addr", cfg, item);
	motr_local_addr = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("ha_addr", cfg, item);
	motr_ha_addr = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("profile", cfg, item);
	motr_prof = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("proc_fid", cfg, item);
	motr_proc_fid = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("index_dir", cfg, item);
	motr_index_dir = get_string_config_value(item, NULL);

	item = NULL;
	WRAP_CONFIG("kvs_fid", cfg, item);
	ifid_str = get_string_config_value(item, NULL);

	return 0;
}

void log_config(void)
{
	log_info("local_addr = %s\n", motr_local_addr);
	log_info("ha_addr    = %s\n", motr_ha_addr);
	log_info("profile    = %s\n", motr_prof);
	log_info("proc_fid   = %s\n", motr_proc_fid);
	log_info("index_dir  = %s\n", motr_index_dir);
	log_info("kvs_fid    = %s\n", ifid_str);
	log_info("---------------------------\n");
}

int init_motr(void)
{
	int rc;
	char  tmpfid[MAXNAMLEN];

	assert(motr_local_addr && motr_ha_addr && motr_prof &&
	       motr_proc_fid);

	/* Initialize Motr configuration */
	motr_conf.mc_is_oostore	= true;
	motr_conf.mc_is_read_verify	= false;
	motr_conf.mc_local_addr	= motr_local_addr;
	motr_conf.mc_ha_addr		= motr_ha_addr;
	motr_conf.mc_profile		= motr_prof;
	motr_conf.mc_process_fid       = motr_proc_fid;
	motr_conf.mc_tm_recv_queue_min_len    = M0_NET_TM_RECV_QUEUE_DEF_LEN;
	motr_conf.mc_max_rpc_msg_size	 = M0_RPC_DEF_MAX_RPC_MSG_SIZE;
	motr_conf.mc_layout_id	= 0;

	/* Index service parameters */
	motr_conf.mc_idx_service_id	= M0_IDX_DIX;
	dix_conf.kc_create_meta		= false;
	motr_conf.mc_idx_service_conf	= &dix_conf;
	motr_conf.mc_is_addb_init	= tsdb_is_engine_on();

	/* Create Motr instance */
	rc = m0_client_init(&motr_instance, &motr_conf, true);
	if (rc != 0) {
		log_err("Failed to initilize Motr\n");
		goto err_exit;
	}

	/* Container is where Entities (object) resides.
	 * Currently, this feature is not implemented in Motr.
	 * We have only single realm: UBER REALM. In future with multiple realms
	 * multiple applications can run in different containers. */
	m0_container_init(&motr_container,
			  NULL, &M0_UBER_REALM,
			  motr_instance);

	rc = motr_container.co_realm.re_entity.en_sm.sm_rc;
	if (rc != 0) {
		log_err("Failed to open uber realm\n");
		goto err_exit;
	}

	motr_uber_realm = motr_container.co_realm;

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

	m0_idx_init(&idx, &motr_container.co_realm,
		    (struct m0_uint128 *)&ifid);

	rc = m0_ufid_init(motr_instance, &ufid_generator);
	if (rc != 0) {
		log_err("Failed to initialise fid generator: %d\n", rc);
		goto err_exit;
	}

	return 0;

err_exit:
	return rc;
}
