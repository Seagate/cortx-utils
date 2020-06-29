#ARG  REDHAT_RELEASE=7.7.1908
FROM ssc-vm-0007.colo.seagate.com:5000/rhel_mero:7.7.1908

COPY *.repo /etc/yum.repos.d/
COPY s3rpm.spec .

RUN yum install -y yum-priorities

RUN yum install -y http://ci-storage.mero.colo.seagate.com/releases/master/mero_stub/mero-0.0.0-stub.x86_64.rpm \
                   http://ci-storage.mero.colo.seagate.com/releases/master/mero_stub/mero-devel-0.0.0-stub.x86_64.rpm \
    && yum install -y git-clang-format \
    && yum-builddep -y s3rpm.spec \
    && rm -f s3rpm.spec \
    && yum remove -y mero mero-devel \
    && yum clean all \
    && rm -rf /var/cache/yum
