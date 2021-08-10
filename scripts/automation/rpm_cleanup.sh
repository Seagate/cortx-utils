#!/bin/bash
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

dependency_pkgs=(
    "java-1.8.0-openjdk-headless"
    "python3 sshpass"
    "python36-m2crypto"
    "salt"
    "salt-master"
    "salt-minion"
    "glusterfs-server"
    "glusterfs-client"
)

cortx_pkgs=(
    "cortx-prereq"
    "python36-cortx-prvsnr"
    "cortx-prvsnr"
    "cortx-prvsnr-cli"
    "python36-cortx-setup"
    "cortx-node-cli"
    "cortx-cli"
    "cortx-py-utils"
    "cortx-motr"
    "cortx-motr-ivt"
    "cortx-hare"
    "cortx-ha"
    "cortx-s3server"
    "cortx-sspl"
    "cortx-sspl-cli"
    "cortx-libsspl_sec"
    "cortx-libsspl_sec-method_none"
    "cortx-libsspl_sec-method_pki"
    "cortx-csm_agent"
    "cortx-csm_web"
    "udx-discovery"
    "uds-pyi"
    "stats_utils"
    "symas-openldap"
)

# Set directive to remove packages with dependencies.
searchString="clean_requirements_on_remove*"
conffile="/etc/yum.conf"
if grep -q "$searchString" "$conffile"
then
    sed -i "/$searchString/d" "$conffile"
fi
echo "clean_requirements_on_remove=1" >> "$conffile"

# Remove cortx packages
echo "Uninstalling cortx packages"
for pkg in ${cortx_pkgs[@]}; do
    if rpm -qi --quiet "$pkg"; then
        yum remove "$pkg" -y
        if [ $? -ne 0 ]; then
            echo "Failed to uninstall $pkg"
            exit 1
        fi
    else
        echo -e "\t$pkg is not installed"
    fi
done

# Remove cortx dependency packages
echo "Uninstalling dependency packages"
for pkg in ${dependency_pkgs[@]}; do
    if rpm -qi --quiet "$pkg"; then
        yum remove "$pkg" -y
        if [ $? -ne 0 ]; then
            echo "Failed to uninstall $pkg"
            exit 1
        fi
    else
        echo -e "\t$pkg is not installed"
    fi
done