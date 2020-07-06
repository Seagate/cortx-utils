FROM ssc-vm-0279.colo.seagate.com:5000/rhel_eos:7.7.1908

COPY eos_7.7.1908.repo csm-uploads.repo  /etc/yum.repos.d/

# upgrade all
RUN yum --assumeyes upgrade

# install node 
ADD install-node.sh /opt/install-node.sh
RUN sh /opt/install-node.sh v12.13.0

# docker-systemctl-replacement
ADD systemctl-replacement.sh /opt/systemctl-replacement.sh
RUN sh /opt/systemctl-replacement.sh

RUN yum clean all \
    && rm -rf /var/cache/yum
