/*
 * Filename: request-handler.c
 * Description: Control request handler.
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

#include <json/json.h> /* for json_object */
#include "management.h"
#include "internal/management-internal.h"
#include "debug.h" /* dassert() */
#include "common/log.h" /* log_* */

int request_consume_header(evhtp_kv_t* kvobj, void* arg) {
	/* @TODO */
	return 0;
}

struct controller* request_get_controller(struct request *request)
{
	char *api_uri = NULL;
	struct server *server = NULL;
	struct controller *controller = NULL;

	server = request->server;
	api_uri = request->api_uri;
	controller = controller_find_by_api_uri(server, api_uri);

	return controller;
}

struct controller_api* request_get_api(struct request *request)
{
	int rc = 0;
	char *api_name = NULL;
	struct controller_api *api = NULL;
	struct controller *controller = NULL;

	controller = request->controller;
	dassert(controller != NULL);

	api_name = request->api_method;
	rc = controller->api_init(api_name,
				  controller,
				  request,
				  &api);
	if (rc != 0) {
		log_err("Failed to get new controller instance.\n");
		api = NULL;
	}

	return api;
}

void request_free_api(struct request *request)
{
	struct controller *controller = NULL;

	controller = request->controller;
	dassert(controller != NULL);

	controller->api_fini(request->api);
}

int request_validate_headers(struct request *request)
{
	int rc = 0;
	struct http *http = NULL;
	const char *content_length = NULL;

	http = request->http;
	content_length = http->header_find(http->evhtp_req->headers_in,
					   "Content-Length");
	/*
	EOS-12305 : Initially we had a NULL check for content_length and
	returned Error Code 22 in case it was NULL. Content Length is the 
	length of the body (in bytes). For a REST Request the body usually
	contains the parameters of the request. A Request may or may not
	need parameters, so checking for NULL and failing is not recommended.
	*/
	if(content_length == NULL) {
		request->in_content_len = 0;
	}
	else{
		request->in_content_len = atoi(content_length);        
	}

	request->in_remaining_len = request->in_content_len;

	/**
	 * ...
	 * Add more common fs validations
	 * ...
	 */

	return rc;
}

int request_accept_data(struct request *request)
{
	int rc = 0;
	char *req_data = NULL;
	int req_data_length = 0;
	evbuf_t *req_buf = NULL;
	struct json_object *json_req_obj = NULL;
	struct json_tokener *json_tokener = NULL;

	/**
	 * 1. Pull the read data from the request in_buffer.
	 * 2. Initialize json parser.
	 */
	req_buf = request->in_buffer;

	req_data_length = evbuffer_get_length(req_buf);
	req_data = malloc(sizeof(char) * req_data_length);
	if (req_data == NULL) {
		rc = ENOMEM;
		goto error;
	}

	evbuffer_copyout(req_buf, (void*)req_data, req_data_length);

	json_tokener = json_tokener_new();
	if (json_tokener == NULL) {
		rc = ENOMEM;
		goto error;
	}

	json_req_obj = json_tokener_parse_ex(json_tokener,
					     req_data,
					     req_data_length);
	if (json_req_obj == NULL) {
		rc = EINVAL;
		log_err("Invalid input json data format : %*.s",
				req_data_length,
				req_data);
		goto error;
	}

	request->in_json_req_obj = json_req_obj;

error:
	if (req_data)
		free(req_data);
	if (json_tokener)
		json_tokener_free(json_tokener);
	return rc;
}

void request_send_response(struct request *request,
			   int code)
{
	char str_resp_size[16];
	const char *str_resp = NULL;
	struct http *http = NULL;
	struct json_object *json_resp_obj = NULL;

	http = request->http;
         
	/* Set CORS Header  */
	request_set_out_header(request,
			       "Access-Control-Allow-Origin",
			       "*");

	if (request->err_code != 0) {
		/**
		 * Set request state to error.
		 * This will avoid further processing of events on the request.
		 * Also each call-back handler of the evhtp_req should check
		 * the state of the request before processing any events.
		 */
		request->state = ERROR;

		/* Create json object */
		request->out_json_req_obj = json_object_new_object();

		json_resp_obj = json_object_new_int(request->err_code);
		json_object_object_add(request->out_json_req_obj,
				       "rc",
				       json_resp_obj);
		json_resp_obj = NULL;

	}

	json_resp_obj = request->out_json_req_obj;

	if (json_resp_obj != NULL) {
		str_resp = json_object_to_json_string(json_resp_obj);
		request->out_content_len = strlen(str_resp);
		sprintf(str_resp_size, "%d", request->out_content_len);

		/* Send error response message. */
                request_set_out_header(request,
                                       "Content-Type",
                                       "application/json");

                request_set_out_header(request,
				       "Accept",
				       "application/json");

		request_set_out_header(request,
				       "Content-Length",
				       str_resp_size);

		request->out_buffer = evbuffer_new();
		evbuffer_add(request->out_buffer,
			     str_resp,
			     request->out_content_len);

		evbuffer_add_buffer(http->evhtp_req->buffer_out,
				    request->out_buffer);

		/**
		 * Free out_json_req_obj out, It will no longer be  used.
		 */
		json_object_put(request->out_json_req_obj);
		request->out_json_req_obj = NULL;

		evbuffer_free(request->out_buffer);
		request->out_buffer = NULL;
	} else {
		request_set_out_header(request, "Content-Length", 0);
	}

	/* Send http reply. */
	http->send_reply(http->evhtp_req, code);

	/**
	 * request->in_json_req_obj will not be used any longer,
	 * you can safely free them here.
	 */
	json_object_put(request->in_json_req_obj);
	request->in_json_req_obj = NULL;
}

void request_set_out_header(struct request *request,
			    const char *key,
			    const char *value)
{
	evhtp_header_t *header = NULL;
	struct http *http = NULL;
	http = request->http;

	header = http->header_new(key, value, 1, 1);
	http->headers_add_header(http->evhtp_req->headers_out, header);
}

void request_execute(struct controller_api *api)
{
	if (!api->request->is_client_disconnected) {
		api->action_table[api->action_next++](api, NULL);
	}
}

void request_next_action(struct controller_api *api)
{
	request_execute(api);
}

int request_get_errcode(struct request *request)
{
	return request->err_code;
}

void request_set_errcode(struct request *request, int err)
{
	request->err_code = err;
}

int request_content_length(struct request *request)
{
	return request->in_content_len;
}

void request_set_readcb(struct request *request, request_read_cb_func cb)
{
	request->read_cb = cb;
}

struct json_object* request_get_data(struct request *request)
{
	return request->in_json_req_obj;
}

void request_set_data(struct request *request, struct json_object *json_obj)
{
	request->out_json_req_obj = json_obj;
}

char* request_api_file(struct request *request)
{
	return request->api_file;
}

int request_init(struct server *server,
		evhtp_request_t *evhtp_req,
		struct request **new_request)
{
	int rc = 0;
	struct http *http = NULL;
	struct request *request = NULL;

	request = calloc(1, sizeof(struct request));
	if (request == NULL) {
		rc = ENOMEM;
		log_err("Request alloc failed : No memory.");
		goto error;
	}

	/* Assign server back link. */
	request->server = server;

	/* Init http request. */
	request->evhtp_req = evhtp_req;
	rc = http_init(evhtp_req, &http);
	if (rc != 0) {
		log_err("http_init failed. rc = %d.\n", rc);
		goto error;
	}
	request->http = http;

	request->http_proto = (enum http_protocol)evhtp_req->proto;
	request->http_method = (enum http_method)evhtp_req->method;

	switch (request->http_method) {
	case HEAD:
		request->api_method = STR_HTTP_METHOD_HEAD;
		break;
	case GET:
		request->api_method = STR_HTTP_METHOD_GET;
		break;
	case PUT:
		request->api_method = STR_HTTP_METHOD_PUT;
		break;
	case DELETE:
		request->api_method = STR_HTTP_METHOD_DELETE;
		break;
	case POST:
		request->api_method = STR_HTTP_METHOD_POST;
		break;
	default:
		request->api_method = STR_HTTP_METHOD_UNKNOWN;
	}

	if (evhtp_req->uri != NULL) {
		if (evhtp_req->uri->path != NULL) {
			request->api_uri =
			evhttp_uridecode(evhtp_req->uri->path->full,
					 1,
					 NULL);

			if (evhtp_req->uri->path->path != NULL) {
				request->api_path =
				evhttp_uridecode(evhtp_req->uri->path->path,
						 1,
						 NULL);
			}

			if (evhtp_req->uri->path->file != NULL) {
				request->api_file =
				evhttp_uridecode(evhtp_req->uri->path->file,
						 1,
						 NULL);
			}
		}

		if (evhtp_req->uri->query_raw != NULL) {
			request->api_query =
			evhttp_uridecode((const char*)evhtp_req->uri->query_raw,
					 1,
					 NULL);
		}
	}

	/* Copy headers. */
	LIST_INIT(&request->in_headers);
	LIST_INIT(&request->out_headers);

	evhtp_kvs_for_each(evhtp_req->headers_in,
			   request_consume_header,
			   request);

	/* Assign InOut param value. */
	*new_request = request;
	request = NULL;
error:
	if (request) {
		if (request->http) {
			free(request->http);
		}

		if (request->api_uri) {
			free(request->api_uri);
			request->api_uri = NULL;
		}

		if (request->api_path) {
			free(request->api_path);
			request->api_path = NULL;
		}

		if (request->api_file) {
			free(request->api_file);
			request->api_file = NULL;
		}

		if (request->api_query) {
			free(request->api_uri);
			request->api_query = NULL;
		}
	}
	return rc;
}

void request_fini(struct request *request)
{
	if (request) {
		if (request->api_uri) {
			free(request->api_uri);
			request->api_uri = NULL;
		}

		if (request->api_path) {
			free(request->api_path);
			request->api_path = NULL;
		}

		if (request->api_file) {
			free(request->api_file);
			request->api_file = NULL;
		}

		if (request->api_query) {
			free(request->api_uri);
			request->api_query = NULL;
		}

		/* http */
		http_fini(request->http);

		/* Cleanup controller api. */
		request_free_api(request);

		/* Delete request object. */
		free(request);
	}
}
