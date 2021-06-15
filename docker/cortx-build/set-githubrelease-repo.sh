#!/bin/bash

set -euf -o pipefail

pip3 install click==7.1.2 && pip3 install githubrelease
mkdir -p /cortx-build-dependencies && cd  /cortx-build-dependencies || exit
export LC_ALL=en_US.utf8
githubrelease asset Seagate/cortx download build-dependencies && /bin/createrepo -v . || exit
yum-config-manager --add-repo file:///cortx-build-dependencies
echo "gpgcheck=0" >> /etc/yum.repos.d/cortx-build-dependencies.repo
yum clean all && rm -rf /var/cache/yum

