/*
 * Filename: management.h
 * Description: Management Module: REST Framewrok for system component management.
 * The management framework provies api's to create the HTTP rest server.
 * We can register "controllers" to it which supports api's for management.
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

/* HOW TO USE?
 *
 * Management framework provides api's to create a RESTFULL HTTP server.
 * And the can be used to overall management of system. We can manage the various
 * services and many more as required by implementig controllers and their apis.
 *
 * The Steps :
 *
 * @code
 *
 * int server_main(int argc, char **argv)
 * {
 * 	...
 *
 *	struct server *server = NULL;
 *	struct params *params = NULL;
 *	struct controller *controller = NULL;
 *
 * 	...
 *
 * 	Parse Params.
 * 	params = params_parse(argc, argv);
 *
 * 	Init Management Sever Instance.
 * 	server = malloc(sizeof(struct server));
 * 	rc = server_init(server, params);
 *
 * 	Register controllers:
 * 	1. Get the controller instance.
 * 	2. Register it.
 *	rc = ctl_{CONTROLLER}_init(server, &controller);
 *	controller_register(server, controller);
 *
 * 	...
 *
 *	Start Control Server.
 *	rc = server_start(server);
 *
 * }
 *
 * @endcode
 *
 * Controller Interfaces:
 * Each controller should implement below methods.
 *
 * @code
 * 	Controller Interface Methods.
 *
 * 	Create an instance of the controller.
 * 	int ctl_{CONTROLLER}_init(struct server *server,
 * 			     struct controller** controller);
 *
 * 	Delete the controller instance.
 * 	void ctl_{CONTROLLER}_fini(struct controller *fs_controller);
 *
 * 	Get controller api instance.
 * 	int {CONTROLLER}_api_init(char *api_name,
 * 				  struct controller *controller,
 * 				  struct request *request,
 * 				  struct controller_api **api);
 *
 *	Free controller api instance.
 * 	void {CONTROLLER}_api_fini(struct controller_api *api)
 *
 * @endcode
 *
 * Controller API Interfaces:
 * Each controller api should implement below methods.
 *
 * @code
 * 	Controller API Interface Methods.
 *
 * 	Create a controller api instance.
 * 	int {CONTROLLER}_{API}_init(struct controller *controller,
 * 				    struct request *request,
 * 				    struct controller_api **api);
 *
 * 	Delete controller api instance.
 * 	void {CONTROLLER}_{API}_fini(struct controller_api *api);
 *
 * @endcode
 *
 * How does it work?
 *
 * The management service uses `libevhtp` to get and put HTTP requests which
 * internally uses `libevent` for eventing mechanism. (See below section :
 * How libevhtp works?). The libevhtp generates various kinds of events on
 * each HTTP request to which we can registers hooks/call-backs to get notified
 * when corresponding event occurs.
 * Firstly, we create instance of evhtp object and bind it to the server IP
 * address and wait for the new connections. Before going to wait for the events
 * we install post_accept call back using evhtp_set_post_accept_cb method.
 * In the post_accept_cb, We then can assign various request callbacks for the
 * incoming requests. The hooks(callbacs) looks like below..
 * evhtp_hook_on_header, evhtp_hook_on_headers, evhtp_hook_on_path,
 * evhtp_hook_on_read, evhtp_hook_on_request_fini etc...
 *
 * For each new connection, we register evhtp_hook_on_headers and
 * evhtp_hook_on_read hooks. The corresponding rquest handlers processes
 * the some part of the request. Each request goes through a standard
 * sequence of steps like - validation, processing, payload handling(if any),
 * response construction and sending. If we get the error in any steps of
 * request processing, we immediatly generates error message and send it back
 * to the client. The remaing steps are skipped if there is error in the
 * previous request processing steps.
 *
 * Initially, We register various controllers(FS, ENPOINT etc..) to the
 * management service. The controllers basically supports of HTTP methods like-
 * GET, PUT and DELETE etc. These controller api's has a logic to handle and
 * process the corresponding HTTP request for the controller.
 * When a new requst comes on the connection we find the controller of the
 * request using requst URI. For example, request on the FS controller looks like:
 * GET http://localhost/fs
 * HOST: localhost
 * The method of HTTP request forms the controller api(here GET). Each controller
 * api has actions method to be called on when that particular events comes.
 *
 * To Summarize The Request State Machine:
 *
 * OnHeaders, OnPayload - external events from libevht.
 * OnHeaders allows us to route (dispatch) the request to the right handler.
 * OnPayload allows us to read out the associated data.
 * OnPayload is an optional event if action does not require payload.
 * When headers or payload cannot be parsed or contain invalid values
 * the server sends out an error.
 * No specific state for errors: in case of errors the request state returns
 * back to the waiting state immediately after sending out a reply that
 * contains the error description.
 *
 * The Request State Daigram:
 *
 *                          +---------------------+------------------>(Send error reply)------------------------+
 *                         /|\                   /|\                                                            |
 *             (can't to parse headers)   (can't get payload)                              		        |
 *                          |                     |                                                             |
 * WaitingForHeaders --(OnHeaders)--> WaitingForPayload --(OnPayload)-[Check request state]--(ERROR)------->(Continue)
 * /\			   |						|					|
 * |			   |						|(RUNNING)				|
 * |		 	   |						|					|
 * |                       |                                            |                   			|
 * |                       |                                            |                    			|
 * |                       +(if no payload expected)------------>(Execute action)           			|
 * |                                                              (Send reply)               			|
 * |                                                                   \|/                  		       \|/
 * +--------------------------------------------------------------------+---------------------------------------+
 *
 * How libevhtp works?
 *
 * #### Bootstrapping
 * 1.	Create a parent evhtp_t structure.
 * 2.	Assign callbacks to the parent for specific URIs or posix-regex based URI's
 * 3.	Optionally assign per-connection hooks (see hooks) to the callbacks.
 * 4.	Optionally assign pre-accept and post-accept callbacks for incoming connections.
 * 5.	Optionally enable built-in threadpool for connection handling (lock-free, and non-blocking).
 * 6.	Optionally morph your server to HTTPS.
 * 7.	Start the evhtp listener.
 * #### Request handling.
 * 1.	Optionally deal with pre-accept and post-accept callbacks if they exist,
 * 	allowing for a connection to be rejected if the function deems it as unacceptable.
 * 2.	Optionally assign per-request hooks (see hooks) for a request
 * 	(the most optimal place for setting these hooks is on a post-accept callback).
 * 3.	Deal with either per-connection or per-request hook callbacks if they exist.
 * 4.	Once the request has been fully processed, inform evhtp to send a reply.
 *
 */

#ifndef _MANAGEMENT_H_
#define _MANAGEMENT_H_

#include <inttypes.h>
#include <sys/queue.h> /* LIST_HEAD, LIST_INIT */
#include <str.h>

struct server;
struct params;
struct request;
struct controller;
struct controller_api;
struct http;

/**
 * ######################################################################
 * #		Control-Server: CONTROL Data Type and APIs.		#
 * ######################################################################
 */
/**
 * Control sever APIs.
 */
int server_main(int argc, char *argv[]);
int server_init(int argc, char *argv[], struct server **server);
int server_fini(struct server *server);
int server_start(struct server *server);
int server_stop(struct server *server);

//@TODO: Move these api's to cortxfs management.h
int management_start(int argc, char *argv[]);
int management_stop(void);
int management_init(void);
int management_fini(void);

/**
 * ######################################################################
 * #		Control-Server: CONTROLLER Data Type and APIs.		#
 * ######################################################################
 */
/**
 * Controller api_new function pointer data types.
 */
typedef int (*controller_api_init_func)(char *api_name,
					struct controller *controller,
					struct request *request,
					struct controller_api **api);
typedef void (*controller_api_fini_func)(struct controller_api *fs_api);

/**
 * Controller - Data Type.
 */
struct controller {
	struct server		*server;   /* Link to struct server instance. */

	/* Controller Fields. */
	const char 		*name;     /* Controller name */
	uint8_t			 type;	   /* User defined controller type,
				              Should be unique. */
	char			*api_uri; /* API uri path. */
	char		       **api_list; /* Controller api list. */
	controller_api_init_func api_init;  /* Controller api new. */
	controller_api_fini_func api_fini; /* Controller api free. */
	LIST_ENTRY(controller)	 entries;  /* Link. */
};

/**
 * Controller - APIs.
 */
void controller_register(struct server *server, struct controller *controller);
void controller_unregister(struct controller *controller);
struct controller* controller_find_by_api_uri(struct server *server,
					       char *api_uri);
struct controller* controller_find_by_name(struct server *server, char *name);

/**
 * ######################################################################
 * #		Control-Server: CONTROLLER-API Data Type and APIs.	#
 * ######################################################################
 */
typedef int (*controller_api_action_func)(struct controller_api *api,
					  void *args);
/**
 * Controller-api - Data Type.
 */
struct controller_api {
	struct controller		*controller;	/* controller. */
	struct request			*request;	/* request. */
	char				*name;		/* api name. */
	int		 	  	 type;		/* api type. */
	int 				 action_next;	/* Next api action */
	controller_api_action_func	*action_table; /* api action table. */
	void				*priv;		/* api private. */
};

struct controller_api_table {
	char	*name;		/* api name. */
	char	*method;	/* api method. */
	int	 id;		/* api id. */
};

/**
 * ######################################################################
 * #		Control-Server: REQUEST data type and APIs.		#
 * ######################################################################
 */
typedef int (*request_read_cb_func)(struct controller_api *api);
struct controller* request_get_controller(struct request *request);
int request_validate_headers(struct request *request);
int request_accept_data(struct request *request);
void request_next_action(struct controller_api *api);
void request_send_response(struct request *request, int code);
int request_content_length(struct request *request);
const char* request_etag_value(struct request *request);
void request_set_input_etag_value(struct request *request,
				  const char *etagstr);
void request_init_etag(struct request *request);
void request_set_reponse_etag_value(struct request *request, str256_t etagstr);
void request_set_readcb(struct request *request, request_read_cb_func cb);
struct json_object* request_get_data(struct request *request);
void request_set_data(struct request *request, struct json_object *json_obj);
char* request_api_file(struct request *request);
int request_get_errcode(struct request *request);
void request_set_errcode(struct request *request, int err_code);
void request_set_out_header(struct request *request,
			    const char *key,
			    const char *value);

/**
 * Utility functions.
 */
int errno_to_http_code(int err_code);

#endif
