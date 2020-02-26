cmake_minimum_required(VERSION 2.6.3)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -lpthread")

SET(framework_LIB_SRCS
	request-handler.c
	params.c
	http.c
	server.c
	controller.c
)

add_library(management_framework OBJECT
		${framework_LIB_SRCS}
	)
