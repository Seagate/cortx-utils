/**
 * Filename: control.c
 * Description: APIs for main.c.
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

#include <sys/queue.h> /* LIST_* */
#include "management.h"
#include "debug.h" /* dassert() */	
#include "common/log.h" /* log_* */

/**
 * Server methods.
 */
int server_init(struct server *server, struct params *params)
{
	int rc = 0;
	int old_cancel_state;

	/* Set control server params. */
	server->params = params; 

	/* Set thread info. */
	server->thread_id = pthread_self();
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, &old_cancel_state);

	/* Init controller_list HEAD. */
	LIST_INIT(&(server->controller_list));

	/* Set control server event base. */
	server->ev_base = event_base_new();
	dassert(server->ev_base != NULL);

	/* Create and init ev_htp instance. */
	if (server->params->bind_ipv4) {
		server->ev_htp_ipv4 = http_evhtp_new(server->ev_base,
						     server);
		dassert(server->ev_htp_ipv4 != NULL);
	}

	if (server->params->bind_ipv6) {
		server->ev_htp_ipv6 = http_evhtp_new(server->ev_base,
						     server);
		dassert(server->ev_htp_ipv6 != NULL);
	}

	/* Server Init. */ 
	LIST_INIT(&(server->request_list));
	server->is_cancelled = 0;
	server->is_launch_err = 0;

	return rc;
}

int server_cleanup(struct server *server)
{
	int rc = 0;
	/* @TODO: Cleanup. */
	free(server);

	return rc;
}

int server_start(struct server *server)
{
	int rc = 0;
	int addr_len = 0;
	char *addr = NULL;
	char *addr_ptr = NULL;
	const char *ipv4_prefix = "ipv4:";
	const char *ipv6_prefix = "ipv6:";

	if (server->params->bind_ipv4) {
		addr_len = strlen(server->params->addr_ipv4);

		addr = malloc((addr_len + 5 + 1) * sizeof(char));
		dassert(addr != NULL);

		addr_ptr = strncpy(addr, ipv4_prefix, 5);
		addr_ptr = strncpy(addr_ptr + 5,
				   server->params->addr_ipv4,
				   addr_len);
		addr_ptr[addr_len+1] = '\0';

		log_info("Starting Control Server on host = %s and port = %d!\n",
			 server->params->addr_ipv4,
			 server->params->port);

		rc = evhtp_bind_socket(server->ev_htp_ipv4,
				       addr,
				       server->params->port, 1024);
		if (rc < 0) {
			log_err("Could not bind socket: %s\n", strerror(errno));
			goto error;
		}

		free(addr);
	}

	if (server->params->bind_ipv6) {
		addr_len = strlen(server->params->addr_ipv6);

		addr = malloc((addr_len + 5) * sizeof(char));
		dassert(addr != NULL);

		addr_ptr = strncpy(addr, ipv6_prefix, 5);
		addr_ptr = strncpy(addr_ptr + 5,
				   server->params->addr_ipv6,
				   addr_len);

		log_info("Starting Control Server on host = %s and port = %d!\n",
			 server->params->addr_ipv6,
			 server->params->port);

		rc = evhtp_bind_socket(server->ev_htp_ipv6,
				       addr,
				       server->params->port, 1024);
		if (rc < 0) {
			log_err("Could not bind socket: %s\n", strerror(errno));
			goto error;
		}

		free(addr);
	}

	/**
	 *  new flag in Libevent 2.1
	 *  EVLOOP_NO_EXIT_ON_EMPTY tells event_base_loop()
	 *  to keep looping even when there are no pending events
	 */
	rc = event_base_loop(server->ev_base, EVLOOP_NO_EXIT_ON_EMPTY);

	return rc;

error:
	if (addr)
		free(addr);
	return rc;
}

int server_stop(struct server *server)
{
	int rc = 0;

	/* @TODO */

	return rc;
}
