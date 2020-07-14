FROM ssc-vm-0279.colo.seagate.com:5000/rhel_eos:7.7.1908

COPY *.repo  /etc/yum.repos.d/

# upgrade all
RUN yum --assumeyes upgrade && \
yum clean all \
&& rm -rf /var/cache/yum

#Fix for cortx-prvsnr installation
RUN yum downgrade systemd-219-67.el7_7.2.x86_64 systemd-libs-219-67.el7_7.2.x86_64 -y

# install node 
ADD install-node.sh /opt/install-node.sh
RUN sh /opt/install-node.sh v12.13.0

# docker-systemctl-replacement
ADD systemctl-replacement.sh /opt/systemctl-replacement.sh
RUN sh /opt/systemctl-replacement.sh

RUN yum clean all \
    && rm -rf /var/cache/yum
