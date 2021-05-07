include_directories(include)
include_directories("/usr/include/motr")

set(MOTR_CFLAGS "-g -D_REENTRANT -D_GNU_SOURCE -DM0_INTERNAL='' -DM0_EXTERN=extern ")
set(MOTR_CFLAGS "${MOTR_CFLAGS} -Wall -Werror -Wno-attributes -Wno-unused-but-set-variable ")
set(MOTR_CFLAGS "${MOTR_CFLAGS} -I/usr/include/motr")

set_source_files_properties(m0log.c PROPERTIES COMPILE_FLAGS  "${CMAKE_C_FLAGS} ${MOTR_CFLAGS}")

SET(LOG_LIB_SRCS
    m0log.c
)

add_library(log OBJECT ${LOG_LIB_SRCS})

