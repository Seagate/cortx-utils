cmake_minimum_required(VERSION 2.6.3)

#include_directories(include)

set(CMAKE_EV_INC /usr/local/include)

include_directories(${CMAKE_EV_INC}/event2)
include_directories(${CMAKE_EV_INC}/evhtp)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -lpthread")


SET(framework_LIB_SRCS
	request.c
	params.c
	http.c
	server.c
	controller.c
)

add_library(management_framework OBJECT
		${framework_LIB_SRCS}
	)
