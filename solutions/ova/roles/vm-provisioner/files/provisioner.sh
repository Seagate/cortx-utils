#!/bin/bash

CORTX_RELEASE_REPO="$1"
CORTX_BASE_PATH=${CORTX_RELEASE_REPO//\/prod\//''}

yum install -y yum-utils
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/3rd_party/"
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}/cortx_iso/"

cat <<EOF >/etc/pip.conf
[global]
timeout: 60
index-url: $CORTX_RELEASE_REPO/python_deps/
trusted-host: $(echo $CORTX_RELEASE_REPO | awk -F '/' '{print $3}')
EOF

# Cortx Pre-requisites
yum install --nogpgcheck -y java-1.8.0-openjdk-headless
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


./script

yum-config-manager --add-repo "${CORTX_BASE_PATH}/dev/"