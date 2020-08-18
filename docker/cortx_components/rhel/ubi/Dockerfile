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

FROM registry.access.redhat.com/ubi7-init

RUN yum install wget -y

RUN wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm && \
    yum install epel-release-latest-7.noarch.rpm -y && \
    yum clean all && rm *.rpm

RUN  yum localinstall http://mirror.centos.org/centos/7/os/x86_64/Packages/openssh-server-7.4p1-21.el7.x86_64.rpm -y && \
    yum install openssh-clients openssh -y && \
    yum remove wget -y && \
    yum clean all

EXPOSE 22