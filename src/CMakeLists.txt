cmake_minimum_required(VERSION 2.6.3)
cmake_policy(SET CMP0017 NEW)

PROJECT(eos-utils C)
set(EOS_UTILS_MAJOR_VERSION 1)
set(EOS_UTILS_MINOR_VERSION 0)
set(EOS_UTILS_PATCH_LEVEL 1)
set(EOS_UTILS_EXTRA_VERSION ${RELEASE_VER})

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC -g")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -I${CMAKE_SOURCE_DIR}/include")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Werror -DDEBUG")

set(EOS_UTILS_BASE_VERSION ${BASE_VERSION})

message( STATUS "cmake version ${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}" )
message( STATUS "eos-utils version ${EOS_UTILS_BASE_VERSION}")

# Option (To enable/disable fault injection.)
option(FAULT_INJECT "Enable Fault Injection." ON)

if (FAULT_INJECT)
        set(BCOND_FAULT_INJECT "%bcond_without")
else (FAULT_INJECT)
        set(BCOND_FAULT_INJECT "%bcond_with")
endif (FAULT_INJECT)

include(CheckIncludeFiles)
include(CheckLibraryExists)

message( STATUS "Fault Injection : ${FAULT_INJECT}")

if (FAULT_INJECT)
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DFAULT_INJECT")
else (FAULT_INJECT)
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
endif(FAULT_INJECT)
	
# Build ancillary libs
add_subdirectory(fault)
set(UTILS_FAULT utils-fault)

# Build log dir
add_subdirectory(log)
set(UTILS_LOG utils-log)

# Build log dir
add_subdirectory(common)
set(UTILS_COMMON utils-common)

# Build eos_helpers dir
#if (USE_MERO_STORE OR USE_KVS_MERO)
add_subdirectory(eos)
set(UTILS_EOS utils-eos)
#endif (USE_MERO_STORE OR USE_KVS_MERO)

# Build management dir
add_subdirectory(management)
set(UTILS_MANAGEMENT management_framework)

# Build test
add_subdirectory(test)

# UT
add_subdirectory(ut)
set(UTILS_UT utils-ut)

find_library(HAVE_CMOCKA cmocka)

if((NOT HAVE_CMOCKA))
	message (FATAL ERROR "Cannot find cmocka")
endif((NOT HAVE_CMOCKA))

set(CMAKE_EV_LIB /usr/local/lib)
link_directories(${CMAKE_EV_LIB})

add_library(eos-utils SHARED
		$<TARGET_OBJECTS:${UTILS_FAULT}>
		$<TARGET_OBJECTS:${UTILS_LOG}>
		$<TARGET_OBJECTS:${UTILS_EOS}>
		$<TARGET_OBJECTS:${UTILS_COMMON}>
		$<TARGET_OBJECTS:${UTILS_UT}>
		$<TARGET_OBJECTS:${UTILS_MANAGEMENT}>
	)


target_link_libraries(eos-utils
	cmocka
	event
	ssl
	crypto
	event_openssl
	evhtp
	json
)

# CPack / rpmbuild specific stuff
set(CPACK_PACKAGE_FILE_NAME "eos-utils-Source" )
set(CPACK_PACKAGE_VENDOR "EOS-UTILS")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "EOS-UTILS - General purpose utilities.")
SET(CPACK_PACKAGE_VERSION_MAJOR ${EOS_UTILS_MAJOR_VERSION})
SET(CPACK_PACKAGE_VERSION_MINOR ${EOS_UTILS_MINOR_VERSION})
SET(CPACK_PACKAGE_VERSION_PATCH ${EOS_UTILS_PATCH_LEVEL})

# Tell CPack the kind of packages to be generated
set(CPACK_GENERATOR "TGZ")
set(CPACK_SOURCE_GENERATOR "TGZ")

set(CPACK_SOURCE_IGNORE_FILES
  "/.git/;/.gitignore/;/.bzr/;~$;${CPACK_SOURCE_IGNORE_FILES}")

include(CPack)

set(PKG_NAME "${CPACK_PACKAGE_NAME}.tar.gz")
add_custom_target(dist COMMAND ${CMAKE_MAKE_PROGRAM} package_source)

if (CONFIGURE)
# Create the .pc file
	configure_file(
			"${PROJECT_SOURCE_DIR}/../build/eos-utils.pc-in.cmake"
			"${PROJECT_SOURCE_DIR}/build/eos-utils.pc"
		      )

# Now create a useable specfile
	configure_file(
			"${PROJECT_SOURCE_DIR}/../build/eos-utils.spec-in.cmake"
			"${PROJECT_SOURCE_DIR}/build/eos-utils.spec"
		      )
endif(CONFIGURE)

set(RPMDEST "--define '_srcrpmdir ${CMAKE_CURRENT_BINARY_DIR}'")

add_custom_target( rpms DEPENDS dist)
add_custom_command(TARGET rpms
                  COMMAND sh -c "rpmbuild ${RPMDEST} -ta ${CPACK_SOURCE_PACKAGE_FILE_NAME}.tar.gz"
                  VERBATIM
                  DEPENDS dist)

add_custom_target( rpm DEPENDS dist)
add_custom_command(TARGET rpm
                  COMMAND sh -c "rpmbuild ${RPMDEST} -tb ${CPACK_SOURCE_PACKAGE_FILE_NAME}.tar.gz"
                  VERBATIM
                  DEPENDS dist)

add_custom_target( srpm DEPENDS dist)
add_custom_command(TARGET srpm
                  COMMAND sh -c "rpmbuild ${RPMDEST} -ts ${CPACK_SOURCE_PACKAGE_FILE_NAME}.tar.gz"
                  VERBATIM
                  DEPENDS dist)

