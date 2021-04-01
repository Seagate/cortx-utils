#!/bin/bash

CORTX_RELEASE_REPO="$1"
yum install -y yum-utils
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}3rd_party/"
yum install --nogpgcheck -y python3 python36-m2crypto salt salt-master salt-minion
rm -rf /etc/yum.repos.d/*3rd_party*.repo
yum-config-manager --add-repo "${CORTX_RELEASE_REPO}cortx_iso/"
yum install --nogpgcheck -y python36-cortx-prvsnr
rm -rf /etc/yum.repos.d/*cortx_iso*.repo
yum clean all
rm -rf /var/cache/yum/

./script
