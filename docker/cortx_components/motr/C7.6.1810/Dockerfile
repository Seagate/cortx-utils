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

#
# Builder image
#

FROM ssc-vm-0279.colo.seagate.com:5000/centos_cortx:7.6.1810 as lustre-rpm-builder

ARG LUSTRE_VERSION

COPY lustre-2.9.0.spec.patch .
ADD  https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/SRPMS/lustre-${LUSTRE_VERSION}-1.src.rpm .

RUN rpm -i lustre-${LUSTRE_VERSION}-1.src.rpm
RUN patch -p1 -i lustre-2.9.0.spec.patch /root/rpmbuild/SPECS/lustre.spec
RUN yum -y install kernel gcc make kernel-devel
RUN yum-builddep -y /root/rpmbuild/SPECS/lustre.spec
RUN QA_RPATHS=255 rpmbuild -bb --without servers --without lustre-tests \
        --define 'configure_args --disable-gss-keyring' \
        --define "kver `ls -1r /lib/modules | head -n1`" \
        /root//rpmbuild/SPECS/lustre.spec

#
# Final image
#
FROM ssc-vm-0279.colo.seagate.com:5000/centos_cortx:7.6.1810

ARG LUSTRE_VERSION

COPY --from=lustre-rpm-builder /root/rpmbuild/RPMS/x86_64/lustre-client-devel-${LUSTRE_VERSION}*.rpm .

RUN wget https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/RPMS/x86_64/kmod-lustre-client-${LUSTRE_VERSION}-1.el7.x86_64.rpm \
         https://downloads.whamcloud.com/public/lustre/lustre-${LUSTRE_VERSION}/el7/client/RPMS/x86_64/lustre-client-${LUSTRE_VERSION}-1.el7.x86_64.rpm

RUN yum --assumeyes install \
        kmod-lustre-client-${LUSTRE_VERSION}*.rpm \
        lustre-client-${LUSTRE_VERSION}*.rpm \
        lustre-client-devel-${LUSTRE_VERSION}*.rpm

COPY *.repo /etc/yum.repos.d/

COPY cortx-motr.spec .
RUN sed -i 's/@.*@/111/g' cortx-motr.spec
RUN kernel_src=$(ls -1rd /lib/modules/*/build | head -n1) \
    yum-builddep -y cortx-motr.spec

RUN rm -f cortx-motr.spec

