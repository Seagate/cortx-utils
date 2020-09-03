#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

FROM registry.access.redhat.com/rhel7-init:7.7

ARG REDHAT_RELEASE
ARG USER_PASS

LABEL maintainer="Cortx Release Engineering"

COPY cortx_uploads.repo /etc/yum.repos.d/

#Enable optional rpms

RUN  yum-config-manager --enable rhel-7-server-optional-rpms \
        yum clean all && \
        rm -rf /var/cache/yum

# install common tools
RUN yum -y upgrade --exclude=redhat-release-server &&  yum -y install python3{,-{devel,pip,setuptools}} \
rpm-build \
openssl-devel \
libffi-devel createrepo file git \
jq \
rpm-build \
rpmdevtools \
scl-utils \
wget \
which \
openssh-server \
java-1.8.0-openjdk \
make \
gcc \
cmake \
gcc-c++ \
yum clean all && \
rm -rf /var/cache/yum

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
