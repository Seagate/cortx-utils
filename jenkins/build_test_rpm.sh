#!/bin/bash
#
# Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

set -e
PROG_NAME=$(basename "$0")
BASE_DIR=$(realpath $(dirname "$0")/../py-utils/test)
BUILD_NUMBER=
GIT_VER=

#Following Install_path should be in sync with cortx.conf.sample config file.
INSTALL_PATH=/opt/seagate

usage() {
    echo """usage: $PROG_NAME [-v version] [-g git_version] [-b build_number]""" 1>&2;
    exit 1;
}

# Check for passed in arguments
while getopts ":g:v:b:" o; do
    case "${o}" in
        v)
            VER=${OPTARG}
            ;;
        g)
            GIT_VER=${OPTARG}
            ;;
        b)
            BUILD_NUMBER=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

[ -z $"$GIT_VER" ] && GIT_VER="$(git rev-parse --short HEAD)" \
        || GIT_VER="${GIT_VER}_$(git rev-parse --short HEAD)"
[ -z "$VER" ] && VER="1.0.0"
[ -z "$BUILD_NUMBER" ] && BUILD_NUMBER=1
REL="${BUILD_NUMBER}_${GIT_VER}"

# Change cwd to py-utils/test
cd "$BASE_DIR"

# Create version file
echo $VER > VERSION
/bin/chmod +rx VERSION

# Update install_path in test-post-install
sed -i -e "s|<INSTALL_PATH>|${INSTALL_PATH}|g" test-post-install

# Update install_path in test-post-uninstall
sed -i -e "s|<INSTALL_PATH>|${INSTALL_PATH}|g" test-post-uninstall

echo "Creating cortx-py-utils-test RPM with version $VER, release $REL"

# Create the rpm
/bin/python3.6 setup.py bdist_rpm --requires cortx-py-utils \
--release="$REL" --post-install test-post-install \
--post-uninstall test-post-uninstall
if [ $? -ne 0 ]; then
  echo "build failed"
  exit 1
fi
