prefix=/usr
exec_prefix=/usr/bin
libdir=/usr/lib64
includedir=/usr/include

Name: @PROJECT_NAME@
Description: General Purpose EOS Utilities.
#Requires:
Version: @LIBUTILS_BASE_VERSION@
Cflags: -I/usr/include/@PROJECT_NAME@/include
Libs: -L/usr/lib64 -L@PROJECT_NAME@

