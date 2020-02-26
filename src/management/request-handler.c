/**
 * Filename: request.c
 * Description: Control request handler.
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

#include <json/json.h> /* for json_object */
#include "management.h"
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
	if (content_length == NULL) {
		/**
		 * Invalid fs request.
		 * Send error responce.
		 */
		rc = EINVAL;
		goto error;
	}

	request->in_content_len = atoi(content_length);
	request->in_remaining_len = request->in_content_len;

	/**
	 * ...
	 * Add more common fs validations
	 * ...
	 */

error:
	return rc;
}

int request_accept_data(struct request *request)
{
	int rc = 0;
	char *req_data = NULL;
	evbuf_t *req_buf = NULL;
	struct json_object *json_req_obj = NULL;

	/**
	 * 1. Pull the read data from the request in_buffer.
	 * 2. Initialize json parser.
	 */
	req_buf = request->in_buffer;

	req_data = (char*)evbuffer_pullup(req_buf, evbuffer_get_length(req_buf));
	json_req_obj = json_tokener_parse(req_data);
	request->in_json_req_obj = json_req_obj;

	return rc;
}

void request_send_responce(struct request *request,
			   int code)
{
	struct http *http = NULL;
	evbuf_t *body = NULL;

	http = request->http;
	body = request->out_buffer;
	if ( body != NULL) {
		evbuffer_add_buffer(http->evhtp_req->buffer_out, body);
	} else {
		request_set_out_header(request, "Content-Length", 0);
	}

	http->send_reply(http->evhtp_req, code);
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
	api->action_table[api->action_next++](api, NULL);
}

void request_next_action(struct controller_api *api)
{
	request_execute(api);
}

int request_init(struct server *server,
		evhtp_request_t *evhtp_req,
		struct request **new_request)
{
	int rc = 0;
	char* decoded_uri = NULL;
	struct http *http = NULL;
	struct request *request = NULL;

	request = malloc(sizeof(struct request));
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

	/* Default request->api_* */
	request->api_uri = NULL;
	request->api_path = NULL;
	request->api_file = NULL;
	request->api_query = NULL;

	if (evhtp_req->uri != NULL) {
		if (evhtp_req->uri->path != NULL) {
			decoded_uri =
			evhttp_uridecode(evhtp_req->uri->path->full,
					 1,
					 NULL);
			request->api_uri = decoded_uri;

			if (evhtp_req->uri->path->path != NULL) {
				decoded_uri =
				evhttp_uridecode(evhtp_req->uri->path->path,
						 1,
						 NULL);
				request->api_path = decoded_uri;
			}

			if (evhtp_req->uri->path->file != NULL) {
				decoded_uri =
				evhttp_uridecode(evhtp_req->uri->path->file,
						 1,
						 NULL);
				request->api_file = decoded_uri;
			}
		}
		
		if (evhtp_req->uri->query_raw != NULL) {
			decoded_uri =
			evhttp_uridecode((const char*)evhtp_req->uri->query_raw,
					 1,
					 NULL);
			request->api_query = decoded_uri;
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

error:
	return rc;
}

void request_fini(struct request *request)
{
	/**@TODO:
	 * Implement request fini method.
	 */
} 
