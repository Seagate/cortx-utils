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

/******************************************************************************/
int str256_from_cstr(str256_t *dst, const char *src, size_t src_len)
{
	int rc = 0;

	dassert(src_len != 0 && src_len <= sizeof(dst->s_str));

	if (unlikely(src_len > sizeof(dst->s_str) - 1)) {
		rc = -EINVAL;
		goto out;
	}

	memset(dst->s_str, 0, sizeof(dst->s_str));
	memcpy(dst->s_str, src, src_len);
	dst->s_str[src_len] = '\0';
	dst->s_len = src_len+1;

out:
	return rc;
}
