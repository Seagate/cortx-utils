/**
 * Filename: management.h
 *
 * Description: Management Module: REST Framewrok for system component management.
 * The management framework provies api's to create the HTTP rest server.
 * We can register "controllers" to it which supports api's for management.
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
 * HOW TO USE?
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
 * the some part of the request. For Each request processing follows a standard
 * sequence of steps followed are - validation, processing, payload handling(if any),
 * response construction and sending. If we get the error in any steps of
 * request processing, we immediatly generates error message and send it back
 * to the client. The remaing steps are skipped if there is error in the
 * previous request processing steps.
 *
 * We registers various controllers(FS, ENPOINT etc..) to the management service.
 * The controllers basically supports of HTTP methods like - GET, PUT and
 * DELETE etc. These controller api has a logic to handle and process the
 * corresponding HTTP request for the controller. When a new requst comes on the
 * connection we find the controller of the request using requst URI.
 * For example, request for the FS controller will will like
 * GET http://localhost/fs
 * HOST: localhost
 * The method of HTTP request forms the controller api(here GET). Each controller
 * api has actions method to be called on when that particular events comes.
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

#include <sys/queue.h> /* LIST_HEAD, LIST_INIT */
#include <pthread.h> /* pthread_t */
#include <stdbool.h> /* bool */

struct server;
struct params;
struct request;
struct controller;
struct controller_api;
struct http;

#include "management-internal.h" /* struct controller_api, struct request etc.. */

/**
 * ######################################################################
 * #		Control-Server: CONTROL Data Type and APIs.		#
 * ######################################################################
 */
struct server {
	/* Control server fields. */
	struct params			*params;	/* User params. */
	LIST_HEAD(controller_list,
		  controller)		 controller_list;
	LIST_HEAD(request_list, request) request_list;

	/* Event fields. */
	evbase_t			*ev_base;	/* Event base */

	/* HTTP fileds. */
	evhtp_t				*ev_htp_ipv4;	/* HTTP instance. */
	evhtp_t				*ev_htp_ipv6;	/* HTTP instance. */

	/* Thread Info */
	pthread_t			 thread_id;	/* Thread id. */
	bool				 is_shutting_down; /* Is shutting down? */
	bool				 is_launch_err;	/* Error in thread start */
};

/**
 * Control sever APIs.
 */
int server_init(struct server *server, struct params *params);
int server_start(struct server *server);
int server_stop(struct server *server);
int server_cleanup(struct server *server);
int management_start(int argc, char *argv[]);
int management_stop(void);
int management_init(void);
int management_fini(void);

/**
 * Control server thread APIs.
 */
int server_thread_init();
void* server_thread_start(void *args); 
int server_thread_cleanup(void);

/**
 * ######################################################################
 * #		Control-Server: CONTROLLER Data Type and APIs.		#
 * ######################################################################
 */

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

/**
 * ######################################################################
 * #		Control-Server: OPTIONS Data Type and APIs.		#
 * ######################################################################
 */

/**
 * Options - Data Type.
 */
struct params {
	/* Address Options. */
	int		 reuse_port;	/* Reuse port. */
	uint16_t	 port;	/* Port number */
	const char	*addr_ipv4;	/* Addr ipv4. */
	const char	*addr_ipv6;	/* Addr ipv6. */
	int		 bind_ipv4;	/* Bind to ipv4 addr. */
	int		 bind_ipv6;	/* Bind to ipv6 addr. */

	/* Local Options */
	int		 print_usage;	/* Print usage */

};

/**
 * Options instance methods.
 */
struct params* params_parse(int argc, char* argv[]);
void params_free(struct params *params);

/**
 * Utility functions.
 */
int errno_to_http_code(int err_code);

#endif
