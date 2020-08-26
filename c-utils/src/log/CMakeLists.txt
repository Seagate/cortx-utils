cmake_minimum_required(VERSION 2.6.3)

SET(LOG_UTILS_SRCS
	log.c
)

add_library(utils-log OBJECT
		${LOG_UTILS_SRCS}
	)
