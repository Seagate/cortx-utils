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

REPO_LIST=(http://gitlab.mero.colo.seagate.com/eos/csm http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr http://gitlab.mero.colo.seagate.com/mero/hare http://gerrit.mero.colo.seagate.com:8080/sspl http://gerrit.mero.colo.seagate.com:8080/s3server http://gerrit.mero.colo.seagate.com:8080/mero)

clone_dir=/root/gitstats
time_zone="Asia/Calcutta"
report_file="../git-stats-report.txt"

#mkdir -p $clone_dir/clone
test -d $clone_dir/clone && $(rm -rf $clone_dir/clone;mkdir -p $clone_dir/clone) || mkdir -p $clone_dir/clone
export TZ=$time_zone;ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
pushd $clone_dir/clone

for repo in "${REPO_LIST[@]}"
do
        echo $repo
         dir=$(echo $repo |  awk -F'/' '{print $NF}')
         git clone --branch master $repo $dir
         pushd $dir
         echo -e "\t--[ $dir stats Report at $(date) ]--" >> $report_file
         echo -e "Githash|Description|Author|" >> $report_file
         git log --date=local --no-merges --pretty=format:"%h|%s|%an|"  --since="12 hours ago">> $report_file
         echo -e "\n" >> $report_file
         echo -e "---------------------------------------------------------------------------------------------" >> $report_file
         popd
done
popd

