/*
 * Filename: error_response.c
 * Description: APIs for error response framework for REST API clients.
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
#include "str.h"  /* str256_t */
#include "common/log.h"
#include <json/json.h>
#include "management.h"
#include "internal/management-internal.h"

/* Format of error response message.
	{
		"error_code": 3,
		"message": "Incorrect Parameters"
	}
*/

int error_resp_get(int code, const char *err_msg, struct error_resp **out_resp)
{
	int rc = 0;
	struct error_resp *resp = NULL;

	resp = calloc(1, sizeof(struct error_resp));
	if (resp == NULL) {
			rc = ENOMEM;
			goto error;
	}

	str256_from_cstr(resp->message, err_msg, strlen(err_msg));
	resp->error_code = code;

	*out_resp = resp;

error:
	log_debug("error response resp=%p, error code =%d", resp, code);

	return rc;
}

void error_resp_tojson(struct error_resp *resp, struct json_object **out_json_resp)
{
	struct json_object *json_obj = NULL;
	struct json_object *json_err_resp = NULL;

	dassert(resp);

	json_err_resp = json_object_new_object();

	json_obj = json_object_new_int(resp->error_code);
	json_object_object_add(json_err_resp,
	                       "error_code", json_obj);

	json_obj = json_object_new_string(STR256_P(&resp->message));
	json_object_object_add(json_err_resp,
	                       "message", json_obj);

	*out_json_resp = json_err_resp;

	log_debug("error response code=%d, error message=" STR256_F,
	          resp->error_code, STR256_P(&resp->message));
}
