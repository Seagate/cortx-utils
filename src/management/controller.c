/**
 * Filename: controller.c
 * Description: Basic controller API.
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

struct controller* controller_find_by_name(struct server *server, char *name)
{
	struct controller *iterator = NULL;
	struct controller *controller = NULL;

	log_debug("Finding controller by name : %s.\n", name);

	LIST_FOREACH(iterator, &server->controller_list, entries) {
		if (!strcmp(iterator->name, name)) {
			controller = iterator;
			break;
		}
	}

	log_debug("Found controller? : %s.\n",
		  (controller != NULL) ? "FOUND" : "NOT FOUND");

	return controller;
}

struct controller* controller_find_by_api_uri(struct server *server,
					      char *api_uri)
{
	struct controller *iterator = NULL;
	struct controller *controller = NULL;

	log_debug("Finding controller by api_uri : %s.\n", api_uri);

	LIST_FOREACH(iterator, &server->controller_list, entries) {
		if (!strncmp(iterator->api_uri,
			     api_uri,
			     strlen(iterator->api_uri))) {
			controller = iterator;
			break;
		}
	}

	log_debug("Found controller? : %s.\n",
		  (controller != NULL) ? "FOUND" : "NOT FOUND");

	return controller;
}

void controller_register(struct server *server, struct controller *controller)
{
	dassert(controller != NULL);

	log_debug("Registering controller : %s.\n", controller->name);

	/* Add to the head. */
	LIST_INSERT_HEAD(&(server->controller_list), controller, entries);

	log_debug("Registered controller : %s.\n", controller->name);
}

void controller_unregister(struct controller *controller)
{
	log_debug("Unregistering controller : %s.\n", controller->name);

	LIST_REMOVE(controller, entries);

	log_debug("Unregistered controller : %s.\n", controller->name);
}
