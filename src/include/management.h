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
 *	rc = {CONTROLLER}_new(server, &controller);
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
 * 	int {CONTROLLER}_init(struct server *server,
 * 			     struct controller** controller);
 *
 * 	Delete the controller instance.
 * 	void {CONTROLLER}_fini(struct controller *fs_controller);
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
 */

#ifndef _MANAGEMENT_H_
#define _MANAGEMENT_H_

#include <sys/queue.h> /* LIST_HEAD, LIST_INIT */
#include <pthread.h> /* pthread_t */

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
	int				 is_cancelled;	/* Is cancelled? */
	int				 is_launch_err;	/* Error in thread start */
};

/**
 * Control sever APIs.
 */
int server_main(int argc, char *argv[]);
int server_init(struct server *server, struct params *params);
int server_start(struct server *server);
int server_cleanup(struct server *server);
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
