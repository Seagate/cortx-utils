ARG CENTOS_RELEASE

FROM centos-systemd:${CENTOS_RELEASE}

ARG CENTOS_RELEASE
ARG USER_PASS

ENV container docker

# Remove all public repos.
RUN rm -rf /etc/yum.repos.d/*.repo
COPY C${CENTOS_RELEASE}.repo eos_${CENTOS_RELEASE}.repo eos_uploads.repo /etc/yum.repos.d/

# upgrade all
RUN yum --assumeyes upgrade

# enable EPEL and SCL repos
RUN yum --assumeyes install centos-release-scl

# install common tools
RUN yum --assumeyes install python3{,-{devel,pip,setuptools}} \
rpm-build \
openssl-devel \
libffi-devel createrepo file git \
jq \
rpm-build \
rpmdevtools \
scl-utils \
sclo-git212 \
wget \
which \
openssh-server \
java-1.8.0-openjdk \
make \
gcc \
cmake \
gcc-c++

# install node 
ADD install-node.sh /opt/install-node.sh
RUN sh /opt/install-node.sh v12.13.0

# enable Git from SLC repo (it's more up to date version)
RUN ln -nsf /opt/rh/sclo-git212/root/bin/* /usr/local/bin/ \
    && ln -nsf /opt/rh/sclo-git212/enable /etc/profile.d/sclo-git212.sh

# set locale
RUN localedef -i en_US -f UTF-8 en_US.UTF-8
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

#Remove sclo repositories
RUN yum-config-manager --disable centos-sclo*

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

CMD ["/usr/sbin/init"]
