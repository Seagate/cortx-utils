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

FROM ssc-vm-0279.colo.seagate.com:5000/centos_motr:7.6.1810

COPY *.repo /etc/yum.repos.d/
COPY s3rpm.spec .

RUN yum install -y yum-priorities

RUN yum install -y http://cortx-storage.colo.seagate.com/releases/cortx/components/github/motr-base/cortx-motr-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
                   http://cortx-storage.colo.seagate.com/releases/cortx/components/github/motr-base/cortx-motr-devel-1.0.0-0_git588b298_3.10.0_1062.el7.x86_64.rpm \
    && yum install -y git-clang-format \
    && yum-builddep -y s3rpm.spec \
    && rm -f s3rpm.spec \
    && yum remove -y motr motr-devel
