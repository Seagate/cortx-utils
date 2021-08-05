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

BUILD_PATH="$1"
BUILD_LOCATION=$(echo "$BUILD_PATH" | sed 's|/mnt/bigstorage|http://cortx-storage.colo.seagate.com|g')
echo -e "Generating README.txt file"
pushd "$BUILD_PATH"
cat <<EOF > README.txt
CONTENTS OF THIS FILE
---------------------

 * Introduction
 * Artifacts
 * Provisioner Guide


Introduction
------------

Cortx Details to be added here.


Artifacts
------------
Release Build location:

$BUILD_LOCATION

Release Info file location:

$BUILD_LOCATION/RELEASE.INFO

Installation
-----------------

Community Build Guide

https://github.com/Seagate/cortx/blob/main/doc/community-build/Building-CORTX-From-Source-for-SingleNode.md

Cortx Deploy Guide

https://github.com/Seagate/cortx/blob/main/doc/community-build/ProvisionReleaseBuild.md

EOF

