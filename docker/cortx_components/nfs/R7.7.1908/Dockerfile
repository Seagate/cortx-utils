FROM ssc-vm-0007.colo.seagate.com:5000/rhel_mero:7.7.1908

COPY *.repo /etc/yum.repos.d/

RUN yum install -y \
        http://ci-storage.mero.colo.seagate.com/releases/eos/components/github/motr-base/cortx-motr-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
        http://ci-storage.mero.colo.seagate.com/releases/eos/components/github/motr-base/cortx-motr-devel-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
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
        dbus-devel \
        redhat-lsb && \
        yum clean all && \
        rm -rf /var/cache/yum

RUN sed -i 's/QA_CHECK_RPATHS=1/QA_CHECK_RPATHS=0/g' ~/.rpmmacros
