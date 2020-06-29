ARG  CENTOS_RELEASE

FROM 10.230.162.34:5000/mero:${CENTOS_RELEASE}

COPY *.repo /etc/yum.repos.d/

RUN yum install -y \ 
	jemalloc \
	jemalloc-devel \
	mero \
	mero-debuginfo \
	mero-devel \
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
