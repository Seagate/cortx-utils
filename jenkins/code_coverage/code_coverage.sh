#!/bin/sh

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

# This script helps to generate coverage report (.xml) for python code

set -e

#variables
SCRIPT_PATH=$(readlink -f "$0")
SCRIPT_DIR=$(dirname "$SCRIPT_PATH")
SRC_DIR="$(dirname "$(dirname "$SCRIPT_DIR" )")"

DES_DIR=${DES_DIR:-"$SRC_DIR/.code_coverage"}

usage() {
    echo """usage: $SCRIPT_PATH [-f framework]""" 1>&2;
    exit 1;
}

die() {
        echo "${*}"
        exit 1
}

# Remove stale coverage reports
cleanup() {
        echo "Cleaning up old coverage reports."
        local file="$DES_DIR/utils_python_coverage.xml"

        if [ -f "$file" ]; then
                rm -f "$file"
        fi
}

# Install any dependency rpms/packages if not present
check_prerequisite() {
        # install coverage.py package if not present
        if ! command -v coverage &>/dev/null; then
                pip3 install coverage
        fi
}


# Run the coverage.py over UTs and generate coverage report
run_coverage() {
  # Running coverage.py tool over UTs
  for test_file in "$SRC_DIR"/py-utils/test/"$FRAMEWORK"/test_*.py
  do
    coverage run -a "$test_file"
  done
  coverage report -m "$SRC_DIR"/py-utils/test/"$FRAMEWORK"/test_*.py

  # Generate xml report
  coverage xml -o "$DES_DIR/utils_python_coverage.xml"
}

# Validate the report generated
check_report() {
        test -f "$DES_DIR/utils_python_coverage.xml" || die "Failed to generate the Coverage report."
}

############################# Main ################################

# Pass the framework
while getopts ":f:" o; do
    case "${o}" in
        f)
            FRAMEWORK=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done

cleanup
check_prerequisite
run_coverage
check_report

echo "Code Coverage Report generated successfully!!"