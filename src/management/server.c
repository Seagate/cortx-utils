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
#include <sys/time.h> /* struct timeval */
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
	evhtp_t *ev_htp_ipv4 = NULL;
	evhtp_t *ev_htp_ipv6 = NULL;
	struct event_base *ev_base = NULL;

	/* Set control server params. */
	server->params = params;

	/* Set thread info. */
	server->thread_id = pthread_self();
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, &old_cancel_state);

	/* Init controller_list HEAD. */
	LIST_INIT(&(server->controller_list));

	/* Set control server event base. */
	ev_base = event_base_new();
	if (ev_base == NULL) {
		log_err("Failed to get event base.");
		goto error;
	}

	/* Create and init ev_htp instance. */
	if (server->params->bind_ipv4) {
		rc = http_evhtp_init(ev_base,
				     server,
				     &ev_htp_ipv4);
		if (rc != 0) {
			log_err("Internal error: http_evhtp_init failed.\n");
			goto error;
		}
	}

	if (server->params->bind_ipv6) {
		rc = http_evhtp_init(ev_base,
				     server,
				     &ev_htp_ipv6);
		if (rc != 0) {
			log_err("Internal error: http_evhtp_init failed.\n");
			goto error;
		}
	}

	/* Server Init. */
	LIST_INIT(&(server->request_list));
	server->is_shutting_down = 0;
	server->is_launch_err = 0;

	server->ev_base = ev_base;
	ev_base = NULL;

	server->ev_htp_ipv4 = ev_htp_ipv4;
	ev_htp_ipv4 = NULL;

	server->ev_htp_ipv6 = ev_htp_ipv6;
	ev_htp_ipv6 = NULL;

error:
	if (ev_htp_ipv4) {
		evhtp_unbind_socket(ev_htp_ipv4);
		evhtp_free(ev_htp_ipv4);
	}

	if (ev_htp_ipv6) {
		evhtp_unbind_socket(ev_htp_ipv4);
		evhtp_free(ev_htp_ipv6);
	}

	if (ev_base) {
		event_base_free(ev_base);
	}

	return rc;
}

int server_cleanup(struct server *server)
{
	int rc = 0;
	if (server == NULL) {
		goto out;
	}

	if (server->params) {
		free(server->params);
	}

	if (server->ev_htp_ipv4) {
		http_evhtp_fini(server->ev_htp_ipv4);
	}

	if (server->ev_htp_ipv6) {
		http_evhtp_fini(server->ev_htp_ipv6);
	}

	if (server->ev_base) {
		event_base_free(server->ev_base);
	}

	free(server);
out:
	return rc;
}

int server_start(struct server *server)
{
	int rc = 0;
	int addr_len = 0;
	int prefix_len = 0;
	char *addr = NULL;
	char *addr_ptr = NULL;
	const char *ipv4_prefix = "ipv4:";
	const char *ipv6_prefix = "ipv6:";

	if (server->params->bind_ipv4) {
		prefix_len = strlen(ipv4_prefix);
		addr_len = strlen(server->params->addr_ipv4);

		addr = malloc((addr_len + prefix_len + 1) * sizeof(char));
		dassert(addr != NULL);

		strncpy(addr, ipv4_prefix, prefix_len);
		strncpy(addr + prefix_len,
			server->params->addr_ipv4,
			addr_len);
		addr[prefix_len + addr_len] = '\0';

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
		prefix_len = strlen(ipv4_prefix);
		addr_len = strlen(server->params->addr_ipv6);

		addr = malloc((addr_len + prefix_len + 1) * sizeof(char));
		dassert(addr != NULL);

		strncpy(addr, ipv6_prefix, prefix_len);
		strncpy(addr_ptr + prefix_len,
			server->params->addr_ipv6,
			addr_len);
		addr[prefix_len + addr_len] = '\0';

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
	 * New flag in Libevent 2.1
	 * EVLOOP_NO_EXIT_ON_EMPTY tells event_base_loop()
	 * to keep looping even when there are no pending events
	 * Removing EVLOOP_NO_EXIT_ON_EMPTY. It is not supported in 1.2.18.
	 */
	rc = event_base_loop(server->ev_base, 0);

	return rc;

error:
	if (addr)
		free(addr);
	return rc;
}

int server_stop(struct server *server)
{
	int rc = 0;
	struct timeval loopexit_timeout = {.tv_sec = 0, .tv_usec = 0};

	if (!server) {
		goto out;
	}

	/* Stop accepting anymore request. */
	server->is_shutting_down = 1;

	loopexit_timeout.tv_sec = 3;	/* Configurable paramater. */
	loopexit_timeout.tv_usec = 0;

 	/**
	 * event_base_loopexit() will let event loop serve all events as usual
	 * till loopexit_timeout. After the timeout, all active events will be
	 * served and then the event loop breaks.
	 */
	rc = event_base_loopexit(server->ev_base, &loopexit_timeout);
	if (rc == 0) {
		log_debug("event_base_loopexit returns SUCCESS.");
	} else {
		log_err("event_base_loopexit returns FAILURE.");
	}
out:
	return rc;
}
