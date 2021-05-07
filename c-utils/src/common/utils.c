/*
 * Filename:         utils.c
 * Description:      common utilities
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

#include <string.h>
#include <errno.h>
#include <utils.h>
#include <common.h>
#include <debug.h>
#include <common/log.h>
#include <common/helpers.h>   /*RC_WRAP_LABEL*/
#include <str.h>
#include <ini_config.h>
#include <m0log.h>
#include <cortx/helpers.h>

static int utils_initialized;

const int utils_magic_symbol = 2810;

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
	return rc;
}

int utils_register_magic_symbol(void)
{
	int rc = 0;
	rc = m0log_add_magic_sym((const void*)&utils_magic_symbol);
	if (rc == 0) {
		log_err("utils could not register magic symbol, rc=%d", rc);
	}
	return rc;
}

int utils_fini(void)
{
	int rc = 0;
	/*TODO conf_fini*/
	return rc;
}
