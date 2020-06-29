FROM registry.access.redhat.com/rhel7-init:7.7

ARG REDHAT_RELEASE
ARG USER_PASS

# upgrade all
RUN yum --assumeyes upgrade

COPY eos_uploads.repo /etc/yum.repos.d/

#Enable optional rpms

RUN  yum-config-manager --enable rhel-7-server-optional-rpms

# install common tools
RUN yum --assumeyes install python3{,-{devel,pip,setuptools}} \
rpm-build \
openssl-devel \
libffi-devel createrepo file git \
jq \
rpm-build \
rpmdevtools \
scl-utils \
# sclo-git212 \
wget \
which \
openssh-server \
java-1.8.0-openjdk \
make \
gcc \
cmake \
gcc-c++


# set locale
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

# set up rpmbuild directory
RUN rpmdev-setuptree

RUN mkdir /var/run/sshd
RUN echo "${USER_PASS}" | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN ssh-keygen -P "" -t rsa -f /etc/ssh/ssh_host_rsa_key
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

EXPOSE 22
