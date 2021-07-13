#!/bin/bash
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

ARG CENTOS_RELEASE

FROM centos:${CENTOS_RELEASE} AS base

ARG CENTOS_RELEASE
ARG ENVIRONMENT
ARG GIT_HASH

LABEL maintainer="cortx.opensource@seagate.com" \
      Description="This image is used to build CORTX components" \
      org.opencontainers.image.revision=$GIT_HASH \
      org.opencontainers.image.source="https://github.com/Seagate/cortx/blob/main/doc/Release_Build_Creation.rst"

ENV BASH_ENV "/etc/profile"
ENV GIT_HASH $GIT_HASH
ENV PATH="/root/.nvm/versions/node/v12.13.0/bin:${PATH}"
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

#Disable default repositories. 
RUN rm -rf /etc/yum.repos.d/CentOS-*

#Add Internal and CORTX uploads repository
COPY ./docker/cortx-build/${ENVIRONMENT}/C${CENTOS_RELEASE}.repo /etc/yum.repos.d/

# Install EPEL repo for opensource-ci
RUN if [ "$ENVIRONMENT" = "opensource-ci" ] ; then yum install epel-release -y ; fi && yum clean all \
&& rm -rf /var/cache/yum

# Enable SCL repos
RUN yum install centos-release-scl -y && yum clean all \
&& rm -rf /var/cache/yum

# install common tools
RUN yum -y install python3{,-{devel,pip,setuptools}} \
createrepo \
file \
git \
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
gcc-c++ \
sudo \
python-Levenshtein \
libtool doxygen \
python-pep8 \
openssl-devel \
graphviz check-devel \
userspace-rcu-devel \
libcmocka.x86_64 \
userspace-rcu-devel \
libcmocka-devel.x86_64 \
jemalloc \
json-c-devel \
json-c \
openssl \
openssl-devel \
cmake3 \
jemalloc-devel \
libntirpc \
libini_config-devel \
autoconf \
libtool \
bison \
flex \
openssl-devel \
doxygen \
dbus-devel \
yum-priorities \
expect \
rpm-sign \
genisoimage \
redhat-ls && yum clean all \
&& rm -rf /var/cache/yum

# enable Git from SLC repo (it's more up to date version)
RUN ln -nsf /opt/rh/sclo-git212/root/bin/* /usr/local/bin/ \
    && ln -nsf /opt/rh/sclo-git212/enable /etc/profile.d/sclo-git212.sh

#Remove sclo repositories
RUN yum-config-manager --disable centos-sclo*

# set locale
RUN localedef -i en_US -f UTF-8 en_US.UTF-8

# set up rpmbuild directory
RUN rpmdev-setuptree

# Copy scripts
COPY ./docker/cortx-build/*.sh /opt/

# install node
RUN bash /opt/install-node.sh v12.13.0 \
&& rm -rf /opt/install-node.sh \
&& rm -rf install.sh

# docker-systemctl-replacement
RUN sh /opt/systemctl-replacement.sh \
&& rm -f /opt/systemctl-replacement.sh \
&& rm -f systemctl.py

# For Provisioner
RUN bash /opt/setup_fpm.sh \
&& rm -f /opt/setup_fpm.sh && yum clean all \
&& rm -rf /var/cache/yum \
&& rm -rf rh-ruby23.sh

# yum repo from GitHub Release 
RUN sh /opt/set-githubrelease-repo.sh \
&& yum clean all \
&& rm -rf /var/cache/yum \
&& rm -f /opt/set-githubrelease-repo.sh

# rpm signing
COPY ./scripts/rpm-signing/* /opt/rpm-signing/

RUN  cat /opt/rpm-signing/gpgoptions >>  ~/.rpmmacros && \
     sed -i '/passphrase/d' /opt/rpm-signing/genkey-batch && \
     sed -i -e 's/$argv 1/$argv 0/g' -e 's/${PASSPHRASE}/ /g' -e '/PASSPHRASE/d' /opt/rpm-signing/rpm-sign.sh && \
     /usr/bin/gpg --batch --gen-key /opt/rpm-signing/genkey-batch && \
     /usr/bin/gpg --export -a 'Seagate'  > /opt/rpm-signing/RPM-GPG-KEY-Seagate && \
     rpm --import /opt/rpm-signing/RPM-GPG-KEY-Seagate

# release helper scripts
COPY ./scripts/release_support/build_release_info.sh /opt/release_support/

# cortx-prereq package

COPY ./scripts/third-party-rpm/ /opt/third-party-rpm

# Makefile for build
COPY ./docker/cortx-build/Makefile . 

FROM base as lustre-rpm-builder

ARG LUSTRE_VERSION 
ARG ENVIRONMENT

ADD https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/SRPMS/lustre-${LUSTRE_VERSION}-1.src.rpm . 
RUN rpm -i lustre-${LUSTRE_VERSION}-1.src.rpm 

COPY ./docker/cortx-build/lustre-2.9.0.spec.patch .

RUN patch -p1 -i lustre-2.9.0.spec.patch /root/rpmbuild/SPECS/lustre.spec

RUN yum -y install kernel{,-devel}  \
	&& yum-builddep -y /root/rpmbuild/SPECS/lustre.spec \
        && yum clean all \
        && rm -rf /var/cache/yum
	
RUN QA_RPATHS=255 rpmbuild -bb --without servers --without lustre-tests \
        --define 'configure_args --disable-gss-keyring' \
        --define "kver `ls -1r /lib/modules | head -n1`" \
        /root//rpmbuild/SPECS/lustre.spec

FROM base as io-build 

ARG LUSTRE_VERSION

COPY --from=lustre-rpm-builder /root/rpmbuild/RPMS/x86_64/lustre-client-devel-${LUSTRE_VERSION}*.rpm .

#Install luster packages
RUN yum install -y https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/RPMS/x86_64/kmod-lustre-client-${LUSTRE_VERSION}-1.el7.x86_64.rpm \
         https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/RPMS/x86_64/lustre-client-${LUSTRE_VERSION}-1.el7.x86_64.rpm \
		 && yum install -y lustre-client-devel-${LUSTRE_VERSION}*.rpm \
		 && yum clean all \
		 && rm -rf /var/cache/yum
		 
		 
RUN curl -k https://raw.githubusercontent.com/Seagate/cortx-motr/stable/cortx-motr.spec.in -o cortx-motr.spec \
	&& sed -i 's/@.*@/111/g' cortx-motr.spec \
	&& kernel_src=$(ls -1rd /lib/modules/*/build | head -n1) \
        && yum-builddep -y cortx-motr.spec \
	&& yum clean all \
        && rm -rf /var/cache/yum
