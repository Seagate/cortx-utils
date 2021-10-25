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
IS_TAR=false
FILE=

usage() {
    echo """usage: $PROG_NAME [-f file_path] [-t target_path] [-c components]""" 1>&2;
    exit 1;
}

extract_tar() {
    TARFILE="$1"
    dest="$2"
    tar -xvf "$TARFILE" -C "$dest" &>/dev/null
}

deflate() {
    case "$1" in
        *.tar.gz )
            extract_tar "$1" "$2"
            IS_TAR=true
            ;;
        *)
            echo "Requested SB archeive format: ${1} not supported yet."
            ;;
    esac
}

extract_compfile() {
    entry="$1"
    for file in "$entry"/*
    do
        if [[ "$file" =~ \.tar.gz$ ]]; then
            component=$(basename "$entry")
            tar_name=$(tar -tzf "$file" | head -1 | cut -f1 -d"/")
            if [ "$tar_name" == "$component" ]; then
                dest_path="$DIR_PATH"
            else
                dest_path="$DIR_PATH/$component"
            fi
            extract_tar "$file" "$dest_path"
            rm -rf "$file"
        fi
    done
}

# Check for passed in arguments
while getopts ":f:d:c:" opt; do
    case "${opt}" in
        f)
            FILE=${OPTARG}
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

if [ -z $"$FILE" ];
then
    echo "Supplied support bundle file/path is Invalid"
    exit 1
fi
[ -z "$DEST" ] && DEST="$(pwd)"
[ -z "$COMPONENTS" ] && COMPONENTS="all"

# Extract the Support Bundle Tarball
deflate "$FILE" "$DEST"

if [ "$IS_TAR" = true ]; then
    tar_name=$(tar -tzf "$FILE" | head -1 | cut -f1 -d"/")
    DIR_PATH="$DEST"/"$tar_name"
    cd "$DIR_PATH"
    # Extract the nested component specific tarfiles
    if [ "$COMPONENTS" == "all" ]; then
        for entry in "$DIR_PATH"/*
        do
            extract_compfile "$entry"
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
                    extract_compfile "$entry"
                fi
            done
        done
    fi
fi

echo "Successfully extracted the supplied Support bundle \
archive at requested destination-path: $DEST !!!"
