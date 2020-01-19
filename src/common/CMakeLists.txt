cmake_minimum_required(VERSION 2.6.3)

SET(COMMON_UTILS_SRCS
	utils.c
)

add_library(utils-common OBJECT
		${COMMON_UTILS_SRCS}
)
