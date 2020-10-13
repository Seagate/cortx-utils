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

ENV BASH_ENV "/etc/profile"
ENV PATH="/root/.nvm/versions/node/v12.13.0/bin:${PATH}"
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

#Disable default repositories. 
RUN yum-config-manager --disable base,extras,updates && mv /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bkp

#Add centos-7.7.1908 repository
COPY *.repo /etc/yum.repos.d/

# enable EPEL and SCL repos
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
COPY *.sh /opt/

# install node
RUN bash /opt/install-node.sh v12.13.0

# docker-systemctl-replacement
RUN sh /opt/systemctl-replacement.sh \
&& rm -f /opt/systemctl-replacement.sh

# For Provisioner
RUN bash /opt/setup_fpm.sh \
&& rm -f /opt/setup_fpm.sh && yum clean all \
&& rm -rf /var/cache/yum

FROM base as lustre-rpm-builder

ARG LUSTRE_VERSION 

ADD  https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/SRPMS/lustre-${LUSTRE_VERSION}-1.src.rpm . 
RUN rpm -i lustre-${LUSTRE_VERSION}-1.src.rpm 

COPY lustre-2.9.0.spec.patch .
RUN patch -p1 -i lustre-2.9.0.spec.patch /root/rpmbuild/SPECS/lustre.spec

RUN yum -y install kernel kernel-devel \
	&& yum-builddep -y /root/rpmbuild/SPECS/lustre.spec
	
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

RUN curl -k https://raw.githubusercontent.com/Seagate/cortx-s3server/stable/rpms/s3/s3rpm.spec -o s3rpm.spec \
     && yum install -y http://cortx-storage.colo.seagate.com/releases/cortx/components/github/motr-base/cortx-motr-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
     http://cortx-storage.colo.seagate.com/releases/cortx/components/github/motr-base/cortx-motr-devel-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
    && yum install -y git-clang-format \
    && yum-builddep -y s3rpm.spec \
    && rm -f s3rpm.spec \
    && yum remove -y cortx-motr cortx-motr-devel

ENV HARE_VENV_DIR=$HOME/.hare-venv

RUN mkdir $HARE_VENV_DIR \
    && python3 -m venv $HARE_VENV_DIR

RUN source $HARE_VENV_DIR/bin/activate \
    && pip3 install PyYAML flake8 mypy ply wheel

ADD https://github.com/dhall-lang/dhall-haskell/releases/download/1.26.1/dhall-1.26.1-x86_64-linux.tar.bz2      /var/cache
ADD https://github.com/dhall-lang/dhall-haskell/releases/download/1.26.1/dhall-json-1.4.1-x86_64-linux.tar.bz2  /var/cache

RUN for f in /var/cache/dhall*.tar*; do tar -C /usr/local -xf "$f"; done
