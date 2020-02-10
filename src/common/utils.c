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
#include <str.h>
/******************************************************************************/
void buff_init(buff_t *dest, void *src, size_t src_len)
{
	dest->buf = src;
	dest->len = src_len;
}
