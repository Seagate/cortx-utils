#!/bin/bash
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
BUILD_URL="$1"
NODE1="$2"
CLUSTER_PASS="$3"

CORTX_RELEASE_REPO="${BUILD_URL}"
yum install -y yum-utils
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/3rd_party/"
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/cortx_iso/"

cat <<EOF >/etc/pip.conf
[global]
timeout: 60
index-url: $CORTX_RELEASE_REPO/python_deps/
trusted-host: $(echo "$CORTX_RELEASE_REPO" | awk -F '/' '{print $3}')
EOF

# Cortx Pre-requisites
yum install --nogpgcheck -y python3 cortx-prereq sshpass
# Pre-reqs for Provisioner
yum install --nogpgcheck -y python36-m2crypto salt salt-master salt-minion
# Provisioner API
yum install --nogpgcheck -y python36-cortx-prvsnr

# Cleanup temporary repos
rm -rf /etc/yum.repos.d/*3rd_party*.repo
rm -rf /etc/yum.repos.d/*cortx_iso*.repo
yum clean all
rm -rf /var/cache/yum/
rm -rf /etc/pip.conf

sshpass -p "${CLUSTER_PASS}" provisioner setup_provisioner srvnode-1:"${NODE1}" \
--logfile --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm --config-path ~/config.ini \
--dist-type bundle --target-build "${BUILD_URL}"

provisioner configure_setup ./config.ini 1

salt-call state.apply components.system.config.pillar_encrypt

provisioner pillar_export