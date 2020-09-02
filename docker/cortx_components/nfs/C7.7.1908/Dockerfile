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

FROM ssc-vm-0279.colo.seagate.com:5000/motr:C7.7.1908

COPY *.repo /etc/yum.repos.d/

RUN yum install -y \
        http://cortx-storage.colo.seagate.com/releases/cortx/components/github/motr-base/cortx-motr-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
        http://cortx-storage.colo.seagate.com/releases/cortx/components/github/motr-base/cortx-motr-devel-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
        userspace-rcu-devel \
	libcmocka.x86_64 \
        userspace-rcu-devel \
	libcmocka-devel.x86_64 \
	jemalloc \
        json-c-devel \
 	json-c \
	libevhtp \
	libevhtp-devel \
	libevent \
	libevent-devel \
	openssl \
	openssl-devel \
	cmake3 \
	jemalloc-devel \
	libntirpc \
	nfs-ganesha-vfs \
	libini_config-devel \
	autoconf \
	libtool \
	bison \
	flex \
	openssl-devel \
	doxygen \
	dbus-devel \
	redhat-lsb && \
        yum clean all && \
        rm -rf /var/cache/yum


RUN sed -i 's/QA_CHECK_RPATHS=1/QA_CHECK_RPATHS=0/g' ~/.rpmmacros
