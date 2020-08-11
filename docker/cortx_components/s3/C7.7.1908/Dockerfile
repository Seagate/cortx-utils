ARG  CENTOS_RELEASE=7.6.1810
FROM ssc-vm-0279.colo.seagate.com:5000/mero:${CENTOS_RELEASE}

COPY *.repo /etc/yum.repos.d/
COPY s3rpm.spec .

RUN yum install -y yum-priorities

RUN yum install -y http://cortx-storage.colo.seagate.com/releases/master/mero_stub/mero-0.0.0-stub.x86_64.rpm \
                   http://cortx-storage.colo.seagate.com/releases/master/mero_stub/mero-devel-0.0.0-stub.x86_64.rpm \
    && yum install -y git-clang-format \
    && yum-builddep -y s3rpm.spec \
    && rm -f s3rpm.spec \
    && yum remove -y mero mero-devel
