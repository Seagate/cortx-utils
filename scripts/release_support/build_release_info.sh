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

usage() { echo "Usage: $0 [-b build location] [-v version] [ -t third party location]" 1>&2; exit 1; }

while getopts ":b:v:t:" o; do
    case "${o}" in
        b)
            BUILD_LOCATION=${OPTARG}
            ;;
        t)
            THIRD_PARTY_LOCATION=${OPTARG}
            ;;    
        v)
            VERSION=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${BUILD_LOCATION}" ] || [ -z "${VERSION}" ] || [ -z "${THIRD_PARTY_LOCATION}" ]; then
    usage
fi

echo -e "Generating RELEASE.INFO file"

EXCLUDE_PACKAGES="cortx-motr-devel\|cortx-motr-tests-ut\|cortx-libsspl_sec-devel\|cortx-libsspl_sec-method_pki\|cortx-prvsnr-cli\|cortx-sspl-cli\|cortx-s3iamcli-devel\|cortx-sspl-test"
pushd "$BUILD_LOCATION" || exit
cat <<EOF > RELEASE.INFO
---
NAME: "CORTX"
VERSION: "$VERSION"
THIRD_PARTY_VERSION: $(readlink -f "$THIRD_PARTY_LOCATION" | awk -F '/' '{print $NF}' | sed -e 's/^/\"/g' -e 's/$/\"/g')
BUILD: $(echo "$BUILD_NUMBER" | sed -e 's/^/\"/g' -e 's/$/\"/g')
OS: $(cat /etc/redhat-release | sed -e 's/ $//g' -e 's/^/\"/g' -e 's/$/\"/g')
DATETIME: $(date +"%d-%b-%Y %H:%M %Z" | sed -e 's/^/\"/g' -e 's/$/\"/g')
KERNEL: $(ls cortx-motr-[0-9]*.rpm | sed -e  's/.*3/3/g' -e 's/.x86_64.rpm//g' -e 's/^/\"/g' -e 's/$/\"/g')
COMPONENTS:
$(ls -1 ./*.rpm | sed 's/\.\///g' | grep -v "$EXCLUDE_PACKAGES" |  awk '{ print "    - \""$1"\""}')
EOF
popd || exit

echo -e "Generating THIRD_PARTY_RELEASE.INFO file"
pushd "$THIRD_PARTY_LOCATION"
#find . -type f -name *.rpm | awk -F '/' '{print $NF}' | awk '{ print "    - \""$1"\""}'

cat <<EOF > THIRD_PARTY_RELEASE.INFO
---
NAME: "CORTX"
VERSION: "$VERSION"
BUILD: $(echo "$BUILD_NUMBER" | sed -e 's/^/\"/g' -e 's/$/\"/g')
OS: $(cat /etc/redhat-release | sed -e 's/ $//g' -e 's/^/\"/g' -e 's/$/\"/g')
DATETIME: $(date +"%d-%b-%Y %H:%M %Z" | sed -e 's/^/\"/g' -e 's/$/\"/g')
THIRD_PARTY_VERSION: $(readlink -f "$THIRD_PARTY_LOCATION" | awk -F '/' '{print $NF}' | sed -e 's/^/\"/g' -e 's/$/\"/g')
THIRD_PARTY_COMPONENTS:
EOF
popd

pushd "$THIRD_PARTY_LOCATION"
for dir in $(ls -1 | grep -E -v "repodata|THIRD_PARTY_RELEASE.INFO")
do
echo "Adding rpms from $dir"
cat <<EOF >> THIRD_PARTY_RELEASE.INFO
    "$dir":
$(find -L ./"$dir" -type f -not -path "./lustre/custom/tcp/*" -name '*.rpm' -or -name '*.tar.xz' -or -name '*.tgz' | awk -F '/' '{print $NF}' | awk '{ print "       - \""$1"\""}')
EOF
done
popd

