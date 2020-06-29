ARG  CENTOS_RELEASE

FROM ssc-vm-0007.colo.seagate.com:5000/mero:${CENTOS_RELEASE}

COPY *.repo /etc/yum.repos.d/

RUN yum install -y \
        eos-core{,-devel,-debuginfo} \	
        userspace-rcu-devel \
	libcmocka.x86_64 \
        userspace-rcu-devel \
	libcmocka-devel.x86_64 \
	jemalloc \
        json-c-devel \
 	json-c \
	libevhtp \
	libevhtp-devel \
	libevent \
	libevent-devel \
	openssl \
	openssl-devel \
	cmake3 \
	jemalloc-devel \
	libntirpc \
	nfs-ganesha-vfs \
	libini_config-devel \
	autoconf \
	libtool \
	bison \
	flex \
	openssl-devel \
	doxygen \
	redhat-lsb

RUN sed -i 's/QA_CHECK_RPATHS=1/QA_CHECK_RPATHS=0/g' ~/.rpmmacros
