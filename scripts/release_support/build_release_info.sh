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

BUILD_LOCATION=$1
EXCLUDE_PACKAGES="cortx-motr-devel\|cortx-motr-tests-ut\|cortx-libsspl_sec-devel\|cortx-libsspl_sec-method_pki"
echo -e "Generating RELEASE.INFO file"
pushd "$BUILD_LOCATION" || exit
cat <<EOF > RELEASE.INFO
---
NAME: "CORTX"
VERSION: "1.0.0"
BUILD: $(echo "$BUILD_NUMBER" | sed -e 's/^/\"/g' -e 's/$/\"/g')
OS: $(cat /etc/redhat-release | sed -e 's/ $//g' -e 's/^/\"/g' -e 's/$/\"/g')
DATETIME: $(date +"%d-%b-%Y %H:%M %Z" | sed -e 's/^/\"/g' -e 's/$/\"/g')
KERNEL: $(ls cortx-motr-[0-9]*.rpm | sed -e  's/.*3/3/g' -e 's/.x86_64.rpm//g' -e 's/^/\"/g' -e 's/$/\"/g')
COMPONENTS:
$(ls -1 ./*.rpm | sed 's/\.\///g' | grep -v "$EXCLUDE_PACKAGES" |  awk '{ print "    - \""$1"\""}')
EOF
popd || exit

