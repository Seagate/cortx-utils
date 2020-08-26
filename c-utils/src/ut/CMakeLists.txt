cmake_minimum_required(VERSION 2.6.3)

SET(UT_UTILS_SRCS
	ut.c
)

add_library(utils-ut OBJECT
		${UT_UTILS_SRCS}
	)
