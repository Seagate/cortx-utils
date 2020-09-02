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

#ARG  REDHAT_RELEASE
FROM sc-vm-0279.colo.seagate.com:5000/rhel_motr:7.7.1908

ADD halon-dist.tar.gz .

COPY *.repo /etc/yum.repos.d/

RUN yum -y install \
           binutils-devel \
           gmp-devel \
           leveldb-devel \
           libgenders-devel \
           libyaml-devel \
           ncurses-devel \
           pcre-devel \
           stack

# ghc-options should match the defaults from `h0` script (see DEFAULT_GHC_OPTS)
#RUN cd halon \
#    && stack build --only-dependencies --ghc-options='-g -j2 -O0' \
#    && cd .. \
#    && rm -rf halon

# fix read permissions for some files that created with user-only access
#RUN find ~/.stack \! -perm -o=r -exec chmod a+r '{}' \; -print
