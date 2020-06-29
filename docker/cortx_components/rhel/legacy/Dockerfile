FROM registry.access.redhat.com/rhel7-init

RUN yum install wget -y

RUN wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
    yum install epel-release-latest-7.noarch.rpm -y && \
    yum clean all && rm *.rpm

RUN  yum localinstall http://mirror.centos.org/centos/7/os/x86_64/Packages/openssh-server-7.4p1-21.el7.x86_64.rpm -y && \
    yum install openssh-clients openssh -y && \
    yum remove wget -y && \
    yum clean all

EXPOSE 22
#echo 'newpassword' |passwd root --stdin #to set paswd after login for ssh
#CMD tail -f /dev/null
