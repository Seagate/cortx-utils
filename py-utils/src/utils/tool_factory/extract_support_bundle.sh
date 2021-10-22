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

PROG_NAME=$(basename "$0")
TARFILE=

usage() {
    echo """usage: $PROG_NAME [-f file_path] [-t target_path] [-c components]""" 1>&2;
    exit 1;
}

# Check for passed in arguments
while getopts ":f:d:c:" opt; do
    case "${opt}" in
        f)
            TARFILE=${OPTARG}
            ;;
        d)
            DEST=${OPTARG}
            ;;
        c)
            COMPONENTS=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

if [ -z $"$TARFILE" ];
then
    echo "Required TARFILE path is missing/invalid."
    exit 1
fi
[ -z "$DEST" ] && DEST="$(pwd)"
[ -z "$COMPONENTS" ] && COMPONENTS="all"

# Extract the Support Bundle Tarball
TAR_NAME=$(tar -tzf "$TARFILE" | head -1 | cut -f1 -d"/")

tar -xzf "$TARFILE" -C "$DEST"
DIR_PATH=$DEST/$TAR_NAME
cd "$DIR_PATH"

extract_file() {
    component=$(basename "$1")
    for file in "$1"/*
    do
        if tar -tf "$file" &>/dev/null; then
            comp_tarname=$(tar -tzf "$file" | head -1 | cut -f1 -d"/")
            if [ "$comp_tarname" == "$component" ]; then
                dest_path="$DIR_PATH"
            else
                dest_path="$DIR_PATH/$component"
            fi
            tar -xzf "$file" -C "$dest_path" 
            rm -rf "$file"
        fi
    done
}

# Extract the nested component specific tarfiles
if [ "$COMPONENTS" == "all" ]; then
    for entry in "$DIR_PATH"/*
    do
        extract_file "$entry"
    done
else
    # Replace comma seperated components with space.
    COMPONENTS=${COMPONENTS//,/ }
    COMPONENTS=${COMPONENTS//  / }

    for entry in "$DIR_PATH"/*
    do
        component=$(basename "$entry")
        for comps in $COMPONENTS
        do
            if [ "$component" == "$comps" ]; then
                extract_file "$entry"
            fi
        done
    done
fi

echo "Successfully Extracted the SB tarfile at path:$DEST !!!"
