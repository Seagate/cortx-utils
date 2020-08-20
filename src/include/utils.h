/*
 * Filename:         utils.h
 * Description:      common structures
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

#ifndef _CORTX_UTILS_H_
#define _CORTX_UTILS_H_

#include <stdint.h>
#include <linux/limits.h>
#include <common/log.h>

struct collection_item;

struct buff {
	/** The length of binary buffer. */
	size_t len;
	/** A buffer which stores binary values. */
	void *buf;
} __attribute__((packed));

typedef struct buff buff_t;

/* Initialize buff with given buffer and length of buffer */
void buff_init(buff_t *dest, void *src, size_t src_len);

/* Initialize utils.
 *  
 * @param struct collection_item *cfg_items.
 * 
 * @return 0 if successful, a negative "-errno" value in case of failure.
 */
int utils_init(struct collection_item *cfg_items);

/* finalize utils.
 * 
 * @param void.
 * 
 * @return 0 if successful, a negative "-errno" value in case of failure.
 */
int utils_fini(void);

#endif /* _CORTX_UTILS_H_ */

