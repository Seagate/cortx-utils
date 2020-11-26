cmake_minimum_required(VERSION 2.6.3)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -lpthread")

SET(framework_LIB_SRCS
	request-handler.c
	params.c
	http.c
	server.c
	controller.c
	utils.c
	md5hash.c
	error_response.c
)

SET(hash_SRC
	md5hash.c
)

add_library(management_framework OBJECT
		${framework_LIB_SRCS}
	)

add_library(management_hash OBJECT
		${hash_SRC}
	)
