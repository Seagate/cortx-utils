/*
 * Filename:         utils.c
 * Description:      common utilities
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.
 *
 */

#include <string.h>
#include <errno.h>
#include <utils.h>
#include <common.h>
#include <debug.h>
#include <common/log.h>
#include <common/helpers.h>   /*RC_WRAP_LABEL*/
#include <str.h>
#include <ini_config.h>
#include <m0common.h>

static int utils_initialized;

void buff_init(buff_t *dest, void *src, size_t src_len)
{
	dest->buf = src;
	dest->len = src_len;
}


int utils_init(struct collection_item *cfg_items)
{
        int rc = 0;
	
	dassert(utils_initialized == 0);
        utils_initialized++;

	/*TODO Placeholder, conf_init needs to be finalize*/

 	rc = m0init(cfg_items);
	if (rc != 0) {
		log_err("m0init failed, rc=%d ", rc);
                goto err;
        }

err:
        return rc;
}


int utils_fini(void)
{
	int rc = 0;
	m0fini();

	/*TODO conf_fini*/
	return rc;
}
