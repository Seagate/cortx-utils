/*
 * Filename:         log.c
 * Description:      Contains implementation of basic log APIs.
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
#include <errno.h>
#include <stdarg.h>
#include <time.h>
#include <unistd.h>
#include "debug.h"
#include "common/log.h"
#include <string.h>

#include <stdlib.h>
#include "lib/trace.h"


#include "lib/string.h"            /* m0_strdup */
#include "lib/user_space/types.h"  /* bool */


static FILE *log_fp = NULL;
static log_level_t log_level = LEVEL_TEST;

const static struct {
	log_level_t log_level;
	const char *log_str;
} log_conv [] = {
	{ LEVEL_FATAL, "LEVEL_FATAL"},
	{ LEVEL_ERR, "LEVEL_ERR"},
	{ LEVEL_WARN, "LEVEL_WARN"},
	{ LEVEL_INFO, "LEVEL_INFO"},
	{ LEVEL_TRACE, "LEVEL_TRACE"},
	{ LEVEL_DEBUG, "LEVEL_DEBUG"},
	{ LEVEL_TEST, "LEVEL_TEST"}
};

log_level_t log_level_no(const char *log_level)
{
	int i;

	for(i = 0; i < sizeof(log_conv) / sizeof(log_conv[0]); ++i) {
		if(strcmp(log_level, log_conv[i].log_str) == 0) {
			return log_conv[i].log_level;
		}
	}
	/* Invalid log level, assert out */
	assert(0);
}

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

/* @todo: Motr logging based or circular logging based system */
int log_write(log_level_t level, const char *fmt, ...)
{
	int rc = 0, len;
	va_list args;
	time_t curr_time;
	int pid = getpid();
	//char *str;
	//char *tmp;

	/*if (level > log_level) {
		goto out;
	}*/

	va_start(args, fmt);
	curr_time = time(NULL);
	fprintf(log_fp, "%10lld [%5d] ", (long long)curr_time, pid);
	len = vfprintf(log_fp, fmt, args);
	if (len < 0) {
		rc = -len;
	}

	fflush(log_fp);

	if (level == LEVEL_TEST) {
		//str = (char *) malloc(sizeof(char) * (len+1));
		//vsprintf(str, fmt, args);
		//tmp = m0_strdup(str);
		//M0_LOG(M0_DEBUG, "%s\n", (char *)tmp);
		M0_LOG(M0_DEBUG, "TEST TEST TEST\n");
		//free(str);
	}

	va_end(args);

//out:
	return rc;
}

int log_fini()
{
	fclose(log_fp);
	log_fp = NULL;
	return 0;
}

