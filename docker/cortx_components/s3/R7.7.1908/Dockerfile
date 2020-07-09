FROM ssc-vm-0279.colo.seagate.com:5000/rhel_mero:7.7.1908

COPY *.repo /etc/yum.repos.d/
COPY s3rpm.spec .

RUN yum install -y cortx-motr{,-devel} \
     		   git-clang-format \
                   yum-priorities \
    		   && yum-builddep -y s3rpm.spec \
	           && rm -f s3rpm.spec \
	           && yum clean all \
	           && rm -rf /var/cache/yum
