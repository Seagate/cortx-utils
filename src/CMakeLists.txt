cmake_minimum_required(VERSION 2.6.3)
cmake_policy(SET CMP0017 NEW)

set(PROJECT_NAME_BASE ${PROJECT_NAME_BASE})
set(UTILS_LIB ${PROJECT_NAME_BASE}-utils)

PROJECT(${UTILS_LIB} C)
set(EOS_UTILS_MAJOR_VERSION 1)
set(EOS_UTILS_MINOR_VERSION 0)
set(EOS_UTILS_PATCH_LEVEL 1)
set(EOS_UTILS_EXTRA_VERSION ${RELEASE_VER})

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -I${CMAKE_SOURCE_DIR}/include")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Werror -fPIC -g")

set(EOS_UTILS_BASE_VERSION ${BASE_VERSION})
set(EOS_NSAL_BASE_VERSION ${BASE_VERSION})

message( STATUS "cmake version ${CMAKE_MAJOR_VERSION}.${CMAKE_MINOR_VERSION}" )
message( STATUS "eos-utils version ${EOS_UTILS_BASE_VERSION}")

# Option (To enable/disable fault injection.)
option(FAULT_INJECT "Enable Fault Injection." ON)

if (FAULT_INJECT)
        set(BCOND_FAULT_INJECT "%bcond_without")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DFAULT_INJECT")
else (FAULT_INJECT)
        set(BCOND_FAULT_INJECT "%bcond_with")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
endif (FAULT_INJECT)

message( STATUS "Fault Injection : ${FAULT_INJECT}")

# Option (To enable/disable ENABLE_DASSERT mode.)
option(ENABLE_DASSERT "Enable ENABLE_DASSERT mode." ON)

if (ENABLE_DASSERT)
        set(BCOND_ENABLE_DASSERT "%bcond_without")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DENABLE_DASSERT")
else (ENABLE_DASSERT)
        set(BCOND_ENABLE_DASSERT "%bcond_with")
	set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
endif (ENABLE_DASSERT)

message( STATUS "ENABLE_DASSERT : ${ENABLE_DASSERT}")

# TODO: Add a configure-time option
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DENABLE_TSDB_ADDB")

include(CheckIncludeFiles)
include(CheckLibraryExists)

# Add TSDB sources
add_subdirectory(tsdb)
set(UTILS_TSDB utils-tsdb)

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
#if (USE_MOTR_STORE OR USE_KVS_MOTR)
add_subdirectory(eos)
set(UTILS_EOS utils-eos)
#endif (USE_MOTR_STORE OR USE_KVS_MOTR)

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

add_library(${UTILS_LIB} SHARED
		$<TARGET_OBJECTS:${UTILS_TSDB}>
		$<TARGET_OBJECTS:${UTILS_FAULT}>
		$<TARGET_OBJECTS:${UTILS_LOG}>
		$<TARGET_OBJECTS:${UTILS_EOS}>
		$<TARGET_OBJECTS:${UTILS_COMMON}>
		$<TARGET_OBJECTS:${UTILS_UT}>
		$<TARGET_OBJECTS:${UTILS_MANAGEMENT}>
	)


target_link_libraries(${UTILS_LIB}
	cmocka
	event
	ssl
	crypto
	event_openssl
	evhtp
	json-c
)

# CPack / rpmbuild specific stuff
set(CPACK_PACKAGE_FILE_NAME "${UTILS_LIB}-Source" )
set(CPACK_PACKAGE_VENDOR "${PROJECT_NAME_BASE}-UTILS")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "${PROJECT_NAME_BASE}-UTILS - General purpose utilities.")
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
			"${PROJECT_SOURCE_DIR}/../build/${UTILS_LIB}.pc-in.cmake"
			"${PROJECT_SOURCE_DIR}/build/${UTILS_LIB}.pc"
		      )

# Now create a useable specfile
	configure_file(
			"${PROJECT_SOURCE_DIR}/../build/${UTILS_LIB}.spec-in.cmake"
			"${PROJECT_SOURCE_DIR}/build/${UTILS_LIB}.spec"
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

