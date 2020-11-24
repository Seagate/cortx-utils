cmake_minimum_required(VERSION 2.6.3)
include_directories(include)
include_directories("/usr/include/motr")

set(MOTR_CFLAGS "-g -D_REENTRANT -D_GNU_SOURCE -DM0_INTERNAL='' -DM0_EXTERN=extern ")
set(MOTR_CFLAGS "${MOTR_CFLAGS} -Wall -Werror -Wno-attributes -Wno-unused-but-set-variable ")
set(MOTR_CFLAGS "${MOTR_CFLAGS} -I/usr/include/motr")

set_source_files_properties(log.c PROPERTIES COMPILE_FLAGS  "${CMAKE_C_FLAGS} ${MOTR_CFLAGS}")
set_source_files_properties(m0log.c PROPERTIES COMPILE_FLAGS  "${CMAKE_C_FLAGS} ${MOTR_CFLAGS}")


SET(LOG_UTILS_SRCS
	log.c
	m0log.c
)

add_library(utils-log OBJECT
		${LOG_UTILS_SRCS}
	)
