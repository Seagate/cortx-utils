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

START_BUILD=$1
TARGET_BUILD=$2
BUILD_LOCATION=$3

function usage() {
echo "No inputs provided exiting..."
echo "Please provide start and target build numbers.Script should be executed as.."
echo "$0 START_BUILD TARGET_BUILD"
exit 1
}

if [ $# -eq 0 ]; then
usage
fi

if [ -z $START_BUILD ]; then echo "No START_BUILD provided.."; exit 1 ; fi
if [ -z $TARGET_BUILD ]; then echo "No TARGET_BUILD provided.."; exit 1; fi

declare -A COMPONENT_LIST=( 
[cortx-s3server]="https://github.com/Seagate/cortx-s3server.git"
[cortx-motr]="https://github.com/Seagate/cortx-motr.git"
[cortx-hare]="https://github.com/Seagate/cortx-hare.git"
[cortx-ha]="https://github.com/Seagate/cortx-ha.git"
[cortx-prvsnr]="https://github.com/Seagate/cortx-prvsnr.git"
[cortx-sspl]="https://github.com/Seagate/cortx-sspl.git"
[cortx-csm_agent]="https://github.com/Seagate/cortx-manager.git"
[cortx-csm_web]="https://github.com/Seagate/cortx-management-portal.git"
[cortx-py-utils]="https://github.com/Seagate/cortx-utils.git"
)

clone_dir="/root/git_build_checkin_stats"
time_zone="Asia/Calcutta"
report_file="../git-build-checkin-report.txt"

#mkdir -p $clone_dir/clone
test -d $clone_dir/clone && $(rm -rf $clone_dir/clone;mkdir -p $clone_dir/clone) || mkdir -p $clone_dir/clone
export TZ=$time_zone;ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

pushd $clone_dir/clone

wget -q $BUILD_LOCATION/$START_BUILD/dev/RELEASE.INFO -O start_build_manifest.txt
wget -q $BUILD_LOCATION/$TARGET_BUILD/dev/RELEASE.INFO -O target_build_manifest.txt

for component in "${!COMPONENT_LIST[@]}"
do
        echo "Component:$component"
        echo "Repo:${COMPONENT_LIST[$component]}"
         dir=$(echo ${COMPONENT_LIST[$component]} |  awk -F'/' '{print $NF}')
         git clone --branch main ${COMPONENT_LIST[$component]} $dir
      	 rc=$?
          if [ $rc -ne 0 ]; then 
          echo "ERROR:git clone failed for $component"
          exit 1
          fi	

                if [ $component == cortx-hare ] || [ $component == cortx-sspl ] || [ $component == cortx-ha ] || [ $component == cortx-py-utils ]; then
                        start_hash=$(grep "$component-" start_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | cut -d. -f1 |  sed 's/git//g'); echo $start_hash
                        target_hash=$(grep "$component-" target_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | cut -d. -f1 |  sed 's/git//g'); echo $target_hash
                elif [ "$component" == "cortx-csm_agent" ] || [ "$component" == "cortx-csm_web" ]; then
                        start_hash=$(grep "$component-" start_build_manifest.txt | head -1 | awk -F['_'] '{print $3}' |  cut -d. -f1); echo $start_hash
                        target_hash=$(grep "$component-" target_build_manifest.txt | head -1 | awk -F['_'] '{print $3}' |  cut -d. -f1); echo $target_hash
                else
                        start_hash=$(grep "$component-" start_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | sed 's/git//g'); echo $start_hash
                        target_hash=$(grep "$component-" target_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | sed 's/git//g'); echo $target_hash
                fi

                 pushd $dir
					
			echo -e "\t--[ Check-ins for $dir from $START_BUILD ($start_hash) to $TARGET_BUILD ($target_hash) ]--" >> $report_file
			echo -e "Githash|Description|Author|" >> $report_file
			change="$(git log "$start_hash..$target_hash" --oneline --pretty=format:"%h|%cd|%s|%an|")";
		if [ "$change" ]; then
			echo "$change" >> $report_file
			else
			echo "No Changes" >> $report_file
			echo -e "\n" >> $report_file
			echo -e "---------------------------------------------------------------------------------------------" >> $report_file
                fi
         popd

done
popd


echo "Printing report"
cat $clone_dir/clone/git-build-checkin-report.txt
