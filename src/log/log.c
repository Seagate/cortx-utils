/*
 * Filename:         log.c
 * Description:      Basic log functions
 *
 * Do NOT modify or remove this copyright and confidentiality notice!
 * Copyright (c) 2019, Seagate Technology, LLC.
 * The code contained herein is CONFIDENTIAL to Seagate Technology, LLC.
 * Portions are also trade secret. Any use, duplication, derivation,
 * distribution or disclosure of this code, for any reason, not expressly
 * authorized is prohibited. All other rights are expressly reserved by
 * Seagate Technology, LLC.
 *
 * Contains implementation of basic log APIs.
 */

#include <stdio.h>
#include <errno.h>
#include <stdarg.h>
#include <time.h>
#include <unistd.h>
#include "debug.h"
#include "log.h"

static FILE *log_fp = NULL;
static log_level_t log_level = LEVEL_INFO;

int log_init(const char *log_path, log_level_t default_level)
{
	int rc = 0;

	dassert(log_fp == NULL);
	log_fp = fopen(log_path, "a+");
	if (log_fp == NULL) {
		rc = errno;
	}
	log_level = default_level;

	return rc;
}

/* @todo: Mero logging based or circular logging based system */
int log_write(log_level_t level, const char *fmt, ...)
{
	int rc = 0, len;
	va_list args;
	time_t curr_time;
	int pid = getpid();

	if (level > log_level) {
		goto out;
	}

	va_start(args, fmt);
	curr_time = time(NULL);
	fprintf(log_fp, "%10lld [%5d] ", (long long)curr_time, pid);
	len = vfprintf(log_fp, fmt, args);
	if (len < 0) {
		rc = -len;
	}

out:
	return rc;
}

int log_fini()
{
	fclose(log_fp);
	log_fp = NULL;
	return 0;
}

