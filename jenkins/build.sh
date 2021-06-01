#!/bin/bash
#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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
BASE_DIR=$(realpath $(dirname "$0")/../py-utils)
BUILD_NUMBER=
GIT_VER=

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

# Change wd to py-utils
cd "$BASE_DIR"

# Create version file
echo $VER > VERSION

# Fetch install_path
INSTALL_PATH=$(grep install_path cortx.conf.sample |  cut -d " " -f 4 | sed -e 's/^"//' -e 's/"$//')

# Put install_path in utils-post-install
sed -i "/#install_path_placeholder/c\install_path=$INSTALL_PATH" utils-post-install

echo "Creating cortx-py-utils RPM with version $VER, release $REL"

# Create the utils-pre-install
echo "#!/bin/bash" > utils-pre-install
echo ""  >> utils-pre-install
echo "PACKAGE_LIST=\""  >> utils-pre-install
/bin/cat requirements.txt >> utils-pre-install
echo "\""  >> utils-pre-install
echo "rc=0
for package in \$PACKAGE_LIST
do
    pip3 freeze | grep \$package > /dev/null
    if [ \$? -ne 0 ]; then
       if [ \$rc -eq 0 ]; then
           echo \"===============================================\"
       fi
       echo \"Required python package \$package is missing\"
       rc=-1
    fi
done
if [ \$rc -ne 0 ]; then
    echo \"Please install above python packages\"
    echo \"===============================================\"
fi
exit \$rc " >> utils-pre-install
/bin/chmod +x utils-pre-install

# Create the rpm
/bin/python3.6 setup.py bdist_rpm --release="$REL" --pre-install utils-pre-install \
 --post-install utils-post-install --post-uninstall utils-post-uninstall
[ $? -ne 0 ] && echo "build failed" && exit 1
