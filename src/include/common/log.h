/*
 * Filename:         log.h
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

#ifndef _LOG_H
#define _LOG_H

#include <stdio.h>

/* @todo : Improve this simplistic implementation of logging. */
#define LOG(level, fmt, ...) \
    log_write(level, "%s: " fmt "\n", __func__, ##__VA_ARGS__)

typedef enum {
    LEVEL_FATAL,
    LEVEL_ERR,
    LEVEL_WARN,
    LEVEL_INFO,
    LEVEL_TRACE,
    LEVEL_DEBUG,
} log_level_t;

#define log_fatal(...) LOG(LEVEL_FATAL, ##__VA_ARGS__)
#define log_err(...) LOG(LEVEL_ERR, ##__VA_ARGS__)
#define log_warn(...) LOG(LEVEL_WARN, ##__VA_ARGS__)
#define log_info(...) LOG(LEVEL_INFO, ##__VA_ARGS__)
#define log_trace(...) LOG(LEVEL_TRACE, ##__VA_ARGS__)

#ifndef DEBUG
#define log_debug(...) LOG(LEVEL_DEBUG, ##__VA_ARGS__)
#else
#define log_debug(...)
#endif /* DEBUG */

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
int log_write(log_level_t level, const char *fmt, ...);

/**
 * Finishes initialized log subsystem
 */
int log_fini();
#endif /* _LOG_H */

