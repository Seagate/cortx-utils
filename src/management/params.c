/**
 * Filename: params.c
 * Description: Server params.
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
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h> /*struct option is defined here*/
#include <errno.h>

#include "management.h"
#include "debug.h" /* dassert() */	
#include "common/log.h" /* log_* */

#define DEFAULT_ADDR_IPV4	"127.0.0.1"
#define DEFAULT_PORT		8081

static struct params default_params = {
	.reuse_port = 0,
	.port = DEFAULT_PORT,

	.bind_ipv4 = 1,
	.bind_ipv6 = 0,

	.addr_ipv4 = DEFAULT_ADDR_IPV4,
	.addr_ipv6 = NULL,

	.print_usage = 0,
};

static struct option opts[] = {
	{ .name = "port",	.has_arg = required_argument,	.val = 'p' },
	{ .name = "reuse-port",	.has_arg = no_argument,		.val = 'r' },
	{ .name = "bind-ipv6",	.has_arg = no_argument,		.val = 'b' },
	{ .name = NULL }
};

struct params* params_parse(int argc, char *argv[])
{
	int c = 0;
	int bind_ipv6 = 0;
	struct params *params = NULL;

	params = malloc(sizeof(struct params));
	dassert(params != NULL);

	/* Init. */
	*params = default_params;

	/* Reinitialize getopt internals. */
	optind = 0;

	while ((c = getopt_long(argc, argv, "p:brh", opts, NULL)) != -1) {
		switch (c) {
		case 'p':
			params->port = atoi(optarg);
			break;
		case 'r':
		 	params->reuse_port = 1;
			break;
		case 'b':
			bind_ipv6 = 1;
			break;
		case 'h':
			params->print_usage = 1;
		default:
			params->print_usage = 1;
			fprintf(stderr, "Bad parameters.\n");
			goto error;
		}
	}

	if (optind != argc) {
		params->print_usage = 1;
		fprintf(stderr, "Bad parameters.\n");
		goto error;
	}

	if (params->reuse_port && bind_ipv6) {
		params->bind_ipv6 = 1;
	}

error:
	return params;
}
