/*
 * Filename: management-test.c
 * Description: Main control.
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

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <getopt.h> /*struct option is defined here */

/* Utils headers. */
#include <management.h>
#include <common/log.h>
#include <debug.h>

/* Local headers. */
#include "echo-controller.h"

/**
 * @brief Print's usage.
 *
 * @param[in] prog 	program name
 */
static void usage(const char *prog)
{
	printf("Usage: %s [OPTIONS]...\n"
		"OPTIONS:\n"
		"\t-p, --port\tControl server port number.\n"
		"\t-r, --reuse-port\tReuse port number for ipv6.\n"
		"\t-b, --bind-ipv6\tBind to ipv6 addr.\n"
		"\t-h, --help\t\tUser help.\n", prog);
}

int main(int argc, char *argv[])
{
	int rc = 0;

	struct server *server = NULL;
	struct params *params = NULL;
	struct controller *controller = NULL;

	/* Get params. */
	params = params_parse(argc, argv);
	if (params->print_usage) {
		rc = 1;
		usage(argv[0]);
		goto free_params;
	}

	/**
	 * @TODO: Enable logger when control server is run in process mode.
	 * rc = log_init(params->log_file, params->log_level);
	 * if (rc != 0) {
	 * 	fprintf(stderr, "Logger init failed, errno : %d.\n", rc);
	 * 	goto free_params;
	 * }
	 */

	/* Get control sever instance. */
	server = malloc(sizeof(struct server));
	if (server == NULL) {
		rc = 1;
		log_err("Server instance malloc failed. Exiting..\n");
		goto free_params;
	}

	/* Init Control Server. */
	rc = server_init(server, params);
	if (rc != 0) {
		log_err("Server init failed. Exiting..\n");
		goto free_server;
	}

	/**
	 * Register controllers:
	 * 1. Get the controller instance.
	 * 2. Register it.
	 */
	controller = echo_new(server);
	dassert(controller != NULL);
	controller_register(server, controller);

	/* Start Control Server. */
	rc = server_start(server);
	if (rc != 0) {
		log_err("Server start failed. Exiting..\n");
		rc = server_cleanup(server);
		goto exit;
	}

free_server:
	free(server);
free_params:
	free(params);
exit:
	return rc;
}
