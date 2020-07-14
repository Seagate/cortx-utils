FROM ssc-vm-0279.colo.seagate.com:5000/rhel_mero:7.7.1908

COPY *.repo /etc/yum.repos.d/
COPY s3rpm.spec .

RUN yum install -y http://ci-storage.mero.colo.seagate.com/releases/eos/components/github/motr-base/cortx-motr-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
                   http://ci-storage.mero.colo.seagate.com/releases/eos/components/github/motr-base/cortx-motr-devel-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
     		   git-clang-format \
                   yum-priorities \
    		   && yum-builddep -y s3rpm.spec \
	           && rm -f s3rpm.spec \
	           && yum clean all \
	           && rm -rf /var/cache/yum
