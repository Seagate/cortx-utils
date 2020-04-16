/**
 * Filename: http.c
 * Description: HTTP APIs.
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

static int http_log_headers(evhtp_header_t *header, void *arg) {
	log_debug("http header(key = '%s', val = '%s')\n",
		  header->key,
		  header->val);
	return 0;
}

static evhtp_res http_on_client_conn_err_callback(evhtp_request_t *evhtp_req,
					     evhtp_error_flags errtype,
					     void *arg)
{
	int rc = EVHTP_RES_OK;
	struct request *request = NULL;

	log_debug("Client disconnected.");

	if (evhtp_req) {
		if (request) {
			request->is_client_disconnected = 1;
		}

		if (evhtp_req->conn) {
			evhtp_unset_all_hooks(&evhtp_req->conn->hooks);
		}

		evhtp_unset_all_hooks(&evhtp_req->hooks);
	}
	return rc;
}

static evhtp_res http_on_client_request_fini(evhtp_request_t *evhtp_req,
					     void *arg)
{
	int rc = EVHTP_RES_OK;
	struct request *request = NULL;

	log_debug("Finalize client request.");

	/**
	 * Around this event libevhtp will free request, so we
	 * protect server code from accessing freed request
	 */
	if (evhtp_req) {
		request = (struct request*)evhtp_req->cbarg;
		if (request) {
			request->is_client_disconnected = 1;
		}

		evhtp_unset_all_hooks(&evhtp_req->hooks);

		/* Free request object. */
		request_fini(request);
	}
	return rc;
}

evhtp_res http_dispatch_request(evhtp_request_t *evhtp_req,
				evhtp_headers_t *hdrs,
				void *arg)
{
	int rc = 0;
	struct server *server = NULL;
	struct request *request = NULL;
	struct controller *controller = NULL;
	struct controller_api *api = NULL;

	log_debug("Received new request.\n");

	server = (struct server*)arg;

	/**
 	 * 1. Parse request.
	 * 2. Find controller.
	 * 3. Find controller api.
	 * 4. Execute api.
	 */

	/* Log headers. */
	evhtp_headers_for_each(hdrs,
			       http_log_headers,
			       evhtp_req->buffer_out);

	/* 1. Parse request. */
	rc = request_init(server, evhtp_req, &request);
	if (rc != 0) {
		/**
		 * Internal Error - Request alloc.
		 */
		log_fatal("Request allocation failed.");
	}

	log_debug("Request Info:\n"
		  "\tHTTP proto : %d\n"
	          "\tHTTP method : %d\n"
		  "\tAPI uri : %s\n"
		  "\tAPI path : %s\n"
		  "\tAPI method : %s\n"
		  "\tAPI query : %s\n",
		  request->http_proto, request->http_method, request->api_uri,
		  request->api_path, request->api_method,
		  (request->api_query == NULL) ? "Empty" : request->api_query);

	/* 2. Find controller. */
	controller = request_get_controller(request);
	if (controller == NULL) {
		/**
		 * No controller found.
		 * Do cleanup and Send error response.
		 */
		log_err("Controller not found : %s.!", request->api_uri);

		request->http->request_pause(evhtp_req);
		evhtp_unset_all_hooks(&evhtp_req->conn->hooks);

		rc = ENOTSUP;
		request->err_code = rc;
		goto error;
	}

	request->controller = controller;

	/* 3. Find controller api. */
	api = request_get_api(request);
	if (api == NULL) {
		/**
		 * No api method found for the controller.
		 * Send error reponce.
		 */
		log_err("Controller API not supported : %s.!",
			request->api_method);

		request->http->request_pause(evhtp_req);
		evhtp_unset_all_hooks(&evhtp_req->conn->hooks);

		rc = ENOTSUP;
		request->err_code = rc;
		goto error;
	}

	request->api = api;

	log_debug("\tController name : %s\n"
		  "\tApi name : %s\n", controller->name, api->name);

	/**
	 * Store request in evhtp_request callback for further processing.
	 * It will be mainly consumed in the http_process_request_data.
	 */
	evhtp_req->cbarg = request;

	/* Check if server is shutting down ot not. */
	if (server->is_shutting_down) {
		request->http->request_pause(evhtp_req);
		evhtp_unset_all_hooks(&evhtp_req->conn->hooks);

		log_err("Controller API not supported : %s.!",
			request->api_method);
		rc = ECONNABORTED;
		request->err_code = rc;
		goto error;
	}

	evhtp_request_set_hook(evhtp_req, evhtp_hook_on_error,
		       (evhtp_hook)http_on_client_conn_err_callback, NULL);

	evhtp_request_set_hook(evhtp_req, evhtp_hook_on_request_fini,
		       (evhtp_hook)http_on_client_request_fini, NULL);

	/* 4. Execute request */
	request_execute(api);

	log_debug("Dispatched new request.\n");

	rc = EVHTP_RES_OK;
	return rc;

error:
	/* Send error response */
	request_send_response(request, errno_to_http_code(rc));
	rc = EVHTP_RES_OK;
	return rc;
}

evhtp_res http_process_request_data(evhtp_request_t *evhtp_req,
				    evbuf_t *buf,
				    void *arg)
{
	int rc = EVHTP_RES_OK;
	size_t req_data_len = 0;
	struct request *request = NULL;
	struct http *http = NULL;

	/* Log request data. */
	log_debug("Received Data: %.*s",
		  (int)evbuffer_get_length(buf),
		  (char *)evbuffer_pullup(buf, evbuffer_get_length(buf)));

	request = (struct request*)evhtp_req->cbarg;

	if (request->ignore_incoming_data || request->in_remaining_len == 0) {
		/* Ingoring incoming request data. */
		goto error;
	}

	if (request->read_cb == NULL) {
		/**
		 * Got the data but read callback is not installed.
		 * It's and internal error.
		 */
		request->err_code = -1;
		request_send_response(request,
				      errno_to_http_code(request->err_code));
		goto error;
	}

	http = request->http;

	request->in_buffer = evbuffer_new();
	evbuffer_add_buffer(request->in_buffer, buf);

	req_data_len = http->evbuffer_get_length(request->in_buffer);
	request->in_read_len = req_data_len;

	request->in_remaining_len -= req_data_len;
	if (request->in_remaining_len != 0) {
		/**
		 * We don't support chunked data.
		 * Send error responce.
		 */
		request->err_code = EINVAL;
		request_send_response(request,
				      errno_to_http_code(request->err_code));
		goto error;
	}

	/* Notify controller api for the incoming data. */
	request->read_cb(request->api);
	log_debug("Dispatched request data.\n");
error:
	if (request->in_buffer) {
		evbuffer_free(request->in_buffer);
		request->in_buffer = NULL;
	}

	return rc;
}

evhtp_res http_set_connection_handlers(evhtp_connection_t *conn, void *arg)
{
	log_info("Setting connection handlers.\n");

	/* Set connection request handlers. */
	evhtp_connection_set_hook(conn,
				  evhtp_hook_on_headers,
				  http_dispatch_request,
				  arg);

	evhtp_connection_set_hook(conn,
				  evhtp_hook_on_read,
				  http_process_request_data,
				  NULL);

	log_info("Set connection handlers.\n");

	return EVHTP_RES_OK;
}

void http_handler(evhtp_request_t *req, void *arg)
{
	/* Placeholder, required to complete the request processing. */
	log_debug("Request Completed.\n");
}

int http_evhtp_init(evbase_t *ev_base,
		   struct server *server,
		   evhtp_t **new_ev_htp)
{
	int rc = 0;
	evhtp_t *ev_htp = NULL;

	log_info("Creating evhtp instance.\n");

	ev_htp = evhtp_new(ev_base, NULL);
	if (ev_htp == NULL) {
		rc = ENOMEM;
		log_err("Internal error : evhtp_new failed.\n");
		goto error;
	}

	log_info("Created evhtp instance.\n");

	/**
	 * So we can support queries like controlserver.com/fs?create or ?list
	 * So we can support empty queries like controlserver.com/fs/list?prefix=
	 */
	evhtp_set_parser_flags(ev_htp,
			       EVHTP_PARSE_QUERY_FLAG_ALLOW_NULL_VALS |
			       EVHTP_PARSE_QUERY_FLAG_ALLOW_EMPTY_VALS);

	/**
	 * Main request processing (processing headers & body) is done in hooks
	 */
	evhtp_set_post_accept_cb(ev_htp,
				 http_set_connection_handlers,
				 server);

	/**
	* This handler is just like complete the request processing & respond
	*/
	evhtp_set_gencb(ev_htp, http_handler, NULL);

	/* Assign InOut param value. */
	*new_ev_htp = ev_htp;
	ev_htp = NULL;

error:
	if (ev_htp) {
		evhtp_free(ev_htp);
	}
	return rc;
}

void http_evhtp_fini(evhtp_t *ev_htp)
{
	if (ev_htp) {
		evhtp_unbind_socket(ev_htp);
		evhtp_free(ev_htp);
		ev_htp = NULL;
	}
}

void http_request_pause(evhtp_request_t *request)
{
	evhtp_request_pause(request);
}

void http_request_resume(evhtp_request_t *request)
{
	evhtp_request_resume(request);
}

evhtp_proto http_request_get_proto(evhtp_request_t *request)
{
	return evhtp_request_get_proto(request);
}

int http_kvs_for_each(evhtp_kvs_t *kvs,
		      evhtp_kvs_iterator cb,
		      void *arg)
{
	return evhtp_kvs_for_each(kvs, cb, arg);
}

const char *http_header_find(evhtp_headers_t *headers, const char *key)
{
	return evhtp_header_find(headers, key);
}

void http_headers_add_header(evhtp_headers_t *headers, evhtp_header_t *header)
{
	evhtp_headers_add_header(headers, header);
}

evhtp_header_t *http_header_new(const char *key,
				const char *val,
				char kalloc,
				char valloc)
{
	return evhtp_header_new(key, val, kalloc, valloc);
}

const char *http_kv_find(evhtp_kvs_t *kvs, const char *key)
{
	return evhtp_kv_find(kvs, key);
}

evhtp_kv_t *http_kvs_find_kv(evhtp_kvs_t *kvs, const char *key)
{
	return evhtp_kvs_find_kv(kvs, key);
}

void http_send_reply(evhtp_request_t *request, evhtp_res code)
{
	evhtp_send_reply(request, code);
}

void http_send_reply_start(evhtp_request_t *request, evhtp_res code)
{
	evhtp_send_reply_start(request, code);
}

void http_send_reply_body(evhtp_request_t *request, evbuf_t *buf)
{
	evhtp_send_reply_body(request, buf);
}

void http_send_reply_end(evhtp_request_t *request)
{
	evhtp_send_reply_end(request);
}

size_t http_evbuffer_get_length(const struct evbuffer *buf)
{
	return evbuffer_get_length(buf);
}

int http_init(evhtp_request_t *evhtp_req, struct http **new_http)
{
	int rc = 0;
	struct http *http = NULL;

	http = malloc(sizeof(struct http));
	if (http == NULL) {
		rc = ENOMEM;
		log_err("Internal error: No memory.");
		goto error;
	}

	http->evhtp_req = evhtp_req;

	/* Assign handlers. */
	http->request_pause		= http_request_pause;
	http->request_resume		= http_request_resume;
	http->request_get_proto		= http_request_get_proto;
	http->kvs_for_each		= http_kvs_for_each;
	http->header_find		= http_header_find;
	http->headers_add_header	= http_headers_add_header;
	http->header_new		= http_header_new;
	http->kv_find			= http_kv_find;
	http->kvs_find_kv		= http_kvs_find_kv;
	http->send_reply		= http_send_reply;
	http->send_reply_start		= http_send_reply_start;
	http->send_reply_body		= http_send_reply_body;
	http->send_reply_end		= http_send_reply_end;
	http->evbuffer_get_length	= http_evbuffer_get_length;

	/* Assign InOut param value. */
	*new_http = http;
	http = NULL;
error:
	if (http) {
		free(http);
	}
	return rc;
}

void http_fini(struct http *http)
{
	free(http);
	http = NULL;
}

