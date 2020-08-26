SET(UTILS_TSDB_SRCS
	tsdb.c
)

add_library(utils-tsdb OBJECT ${UTILS_TSDB_SRCS})

