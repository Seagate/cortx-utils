/*
 * Filename:         log.h
 * Description:      Contains implementation of basic log APIs
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

#ifndef _LOG_H
#define _LOG_H

#include <stdio.h>
#include <stdbool.h>

#define ATTR_FORMAT(_fmt, _va) __attribute__((format(printf, _fmt, _va)))

/* @todo : Improve this simplistic implementation of logging. */
#define LOG(level, fmt, ...) \
    log_write(level, "%s: %d " fmt "\n", __func__, __LINE__, ##__VA_ARGS__)

typedef enum {
    LEVEL_FATAL,
    LEVEL_ERR,
    LEVEL_WARN,
    LEVEL_INFO,
    LEVEL_TRACE,
    LEVEL_DEBUG,
    LEVEL_TEST,
} log_level_t;

#define log_fatal(...) LOG(LEVEL_FATAL, ##__VA_ARGS__)
#define log_err(...) LOG(LEVEL_ERR, ##__VA_ARGS__)
#define log_warn(...) LOG(LEVEL_WARN, ##__VA_ARGS__)
#define log_info(...) LOG(LEVEL_INFO, ##__VA_ARGS__)
#define log_trace(...) LOG(LEVEL_TRACE, ##__VA_ARGS__)
#define log_test(...) LOG(LEVEL_TEST, ##__VA_ARGS__)

#define log_debug(...) LOG(LEVEL_DEBUG, ##__VA_ARGS__)

/**
 * Returns the log level string in log_level_t type
 * @param[in] log level string
 * @return error code. log level in log_level_t in success.
 *         asserts on failure
 */
log_level_t log_level_no(const char *log_level);

/**
 * Initializes log subsystem
 * @param[in] log file path
 * @param[in] default log level
 * @return error code. 0 in success. Non-zero on failure
 */
int log_init(const char *log_path, log_level_t default_level);

/**
 * Writes log onto the log file
 * @param[in] log level 
 * @param[in] format string
 * @param[in] arguments
 * @return error code. 0 in success. Non-zero on failure
 */
int log_write(log_level_t level, const char *fmt, ...) ATTR_FORMAT(2, 3);

/**
 * Finishes initialized log subsystem
 */
int log_fini();
#endif /* _LOG_H */

