set(CORTX_CFLAGS "-D_REENTRANT -D_GNU_SOURCE -DM0_INTERNAL='' -DM0_EXTERN=extern ")
set(CORTX_CFLAGS "${CORTX_CFLAGS} -include config.h ")
set(CORTX_CFLAGS "${CORTX_CFLAGS} -Wall -Werror -Wno-attributes -Wno-unused-but-set-variable ") 
set(CORTX_CFLAGS "${CORTX_CFLAGS} -fno-strict-aliasing -fno-omit-frame-pointer  -fno-common -fPIC ") 
set(CORTX_CFLAGS "${CORTX_CFLAGS} -I/usr/include/motr -I/usr/include/libcfs ")
#set(CORTX_CFLAGS "${CORTX_CFLAGS} -I/usr/include/lustre")

include_directories("/usr/include/motr")

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${CORTX_CFLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${CORTX_CFLAGS}")

set(DEFAULT_CORTXFSINC "")
set(DEFAULT_LIBCORTXFS "")
set(DEFAULT_CORTXUTILSINC "")
set(DEFAULT_LIBCORTXUTILS "")

set(CORTXFSINC ${DEFAULT_CORTXFSINC} CACHE PATH "Path to folder with nsal headers")
set(LIBCORTXFS ${DEFAULT_LIBCORTXFS} CACHE PATH "Path to folder with libcortx-nsal.so")

set(CORTXUTILSINC ${DEFAULT_CORTXUTILSINC} CACHE PATH "Path to folder with fault.h")
set(LIBCORTXUTILS ${DEFAULT_LIBCORTXUTILS} CACHE PATH "Path to folder with libcortx-utils.so")

include_directories(${CORTXFSINC})
link_directories(${LIBCORTXFS})

include_directories(${CORTXUTILSINC})
link_directories(${LIBCORTXUTILS})

SET(cortx_LIB_SRCS
   m0common.c
   m0kvs.c
   m0store.c
)

add_library(utils-cortx OBJECT ${cortx_LIB_SRCS})

