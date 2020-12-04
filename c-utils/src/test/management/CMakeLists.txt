cmake_minimum_required(VERSION 2.8.8)

add_executable(md5hash-test
		 md5hash_test.c
		 $<TARGET_OBJECTS:${UTILS_HASH}>
		 $<TARGET_OBJECTS:${UTILS_LOG}>
	)


target_link_libraries(md5hash-test
	ssl
	crypto
	motr
	)

