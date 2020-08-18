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

ARG  CENTOS_RELEASE

FROM 10.230.162.34:5000/mero:${CENTOS_RELEASE}

COPY *.repo /etc/yum.repos.d/

RUN yum install -y \ 
	jemalloc \
	jemalloc-devel \
	mero \
	mero-debuginfo \
	mero-devel \
	libntirpc \
	nfs-ganesha-vfs \
	libini_config-devel \
	autoconf \
	libtool \
	bison \
	flex \
	openssl-devel \
	doxygen \
	redhat-lsb

RUN sed -i 's/QA_CHECK_RPATHS=1/QA_CHECK_RPATHS=0/g' ~/.rpmmacros
