/*
 * Filename: controller.c
 * Description: Basic controller API.
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
 
#include "management.h"
#include "internal/management-internal.h"
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
