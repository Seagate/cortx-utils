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

FROM ssc-vm-0279.colo.seagate.com:5000/cortx:C7.7.1908

RUN rm -rf /etc/yum.repos.d/CentOS-*.repo

COPY *.repo  /etc/yum.repos.d/

# upgrade all
RUN yum --assumeyes upgrade --exclude=centos-release && \
    yum clean all \
    && rm -rf /var/cache/yum

# install node 
ADD install-node.sh /opt/install-node.sh
RUN sh /opt/install-node.sh v12.13.0

# docker-systemctl-replacement
ADD systemctl-replacement.sh /opt/systemctl-replacement.sh
RUN sh /opt/systemctl-replacement.sh

RUN yum clean all \
    && rm -rf /var/cache/yum
