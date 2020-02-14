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

#include "management.h"
#include "debug.h" /* dassert() */	
#include "common/log.h" /* log_* */

int request_consume_header(evhtp_kv_t* kvobj, void* arg) {
	/* @TODO */
	return 0;
}

struct controller* request_get_controller(struct request *request)
{
	char *api_path = NULL;
	struct server *server = NULL;
	struct controller *controller = NULL;

	server = request->server;	
	api_path = request->api_path;
	controller = controller_find_by_api_path(server, api_path);

	return controller;
}

struct controller_api* request_get_api(struct request *request)
{
	char *api_name = NULL;
	struct controller_api *api = NULL;
	struct controller *controller = NULL;

	controller = request->controller;
	dassert(controller != NULL);

	api_name = request->api_method;
	api = controller->api_new(api_name,
				  controller,
				  request);

	return api;
}

void request_execute(struct controller_api *api)
{
	api->action_table[api->action_next++](api, NULL);
}

struct request* request_new(struct server *server, evhtp_request_t *evhtp_req)
{
	char* decoded_uri = NULL;
	struct request *request = NULL;

	request = malloc(sizeof(struct request));
	if (request == NULL) {
		log_err("Request alloc failed : No memory.");
		goto error;
	}

	/* Assign server back link. */
	request->server = server;

	/* Init http request. */
	request->evhtp_req = evhtp_req;
	request->http = http_new(evhtp_req);

	request->http_method = (enum http_methods)evhtp_req->method;
	request->http_proto = (enum http_protocol)evhtp_req->proto;

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
				request->api_method = decoded_uri;
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

	/* Assign action method. */
	request->execute = request_execute;
	request->next_action = request_execute;

error:
	return request;
}
