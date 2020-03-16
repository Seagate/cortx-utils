/*
 * Filename:         utils.h
 * Description:      common structures
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

#ifndef _EOS_UTILS_H_
#define _EOS_UTILS_H_

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

#endif /* _EOS_UTILS_H_ */

