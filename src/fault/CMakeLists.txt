cmake_minimum_required(VERSION 2.6.3)

SET(FAULT_UTILS_SRCS
	fault.c
	fault-points.c
)

add_library(utils-fault OBJECT
		${FAULT_UTILS_SRCS}
	)
