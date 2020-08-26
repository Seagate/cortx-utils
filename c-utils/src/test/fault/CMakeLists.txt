cmake_minimum_required(VERSION 2.8.8)

add_executable(fault-test
		fault-test.c
		$<TARGET_OBJECTS:${UTILS_FAULT}>
	)
