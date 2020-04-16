/**
 * Filename: utils.c
 * Description: General purpose utility functions.
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation, distribution
 * or disclosure of this code, for any reason, not expressly authorized is
 * prohibited. All other rights are expressly reserved by Seagate Technology, LLC.
 * 
 * Author: Yogesh Lahane <yogesh.lahane@seagate.com>
 *
 */

#include <errno.h>
#include <management.h>

int errno_to_http_code(int err_code)
{
	int http_code;
	switch (err_code) {
	case EPERM:
	case EACCES:
		http_code = EVHTP_RES_UNAUTH;
		break;
	case ENOENT:
		http_code = EVHTP_RES_NOTFOUND;
		break;
	case EINVAL:
		http_code = EVHTP_RES_BADREQ;
		break;
	case EEXIST:
		http_code = EVHTP_RES_CONFLICT;
		break;
	case ENOTSUP:
		http_code = EVHTP_RES_NOTIMPL;
		break;
	case EFBIG:
		http_code = EVHTP_RES_ENTOOLARGE;
		break;
	case ECONNABORTED:
		http_code = EVHTP_RES_SERVUNAVAIL;
		break;
	default:
		http_code = EVHTP_RES_SERVERR;
	}

	return http_code;
}
