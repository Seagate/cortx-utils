/*
 * Filename:         str.c
 * Description:      string utilities
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

#include <errno.h>
#include <ctype.h> /*isalnum*/
#include <str.h>

/******************************************************************************/
int str256_isalphanum(const str256_t *name)
{
	int i, rc = 0;

	for (i=0; name->s_str[i] != '\0' && i < name->s_len; i++) {
		if (!isalnum(name->s_str[i])) {
			rc = -EINVAL;
			break;
		}
	}

	return rc;
}
