#!/bin/bash

START_BUILD=$1
TARGET_BUILD=$2

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

declare -A COMPONENT_LIST=( [eos-s3server]='http://gerrit.mero.colo.seagate.com:8080/s3server'
[eos-core]='http://gerrit.mero.colo.seagate.com:8080/mero'
[eos-hare]='http://gitlab.mero.colo.seagate.com/mero/hare'
[eos-prvsnr]='http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr'
[eos-sspl]='http://gerrit.mero.colo.seagate.com:8080/sspl'
[eos-csm_agent]='http://gitlab.mero.colo.seagate.com/eos/csm'
)

clone_dir="/root/git_build_checkin_stats"
time_zone="Asia/Calcutta"
report_file="../git-build-checkin-report.txt"

#mkdir -p $clone_dir/clone
test -d $clone_dir/clone && $(rm -rf $clone_dir/clone;mkdir -p $clone_dir/clone) || mkdir -p $clone_dir/clone
export TZ=$time_zone;ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

pushd $clone_dir/clone

wget -q http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/$START_BUILD/MANIFEST.MF -O start_build_manifest.txt
wget -q http://ci-storage.mero.colo.seagate.com/releases/eos/integration/centos-7.7.1908/$TARGET_BUILD/MANIFEST.MF -O target_build_manifest.txt

for component in "${!COMPONENT_LIST[@]}"
do
        echo "Component:$component"
        echo "Repo:${COMPONENT_LIST[$component]}"
         dir=$(echo ${COMPONENT_LIST[$component]} |  awk -F'/' '{print $NF}')
         git clone --branch master ${COMPONENT_LIST[$component]}.git $dir
      	 rc=$?
          if [ $rc -ne 0 ]; then 
          echo "ERROR:git clone failed for $component"
          exit 1
          fi	

                if [ $component == eos-hare ] || [ $component == eos-sspl ]; then
                                        start_hash=$(grep $component start_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | cut -d. -f1 |  sed 's/git//g'); echo $start_hash
                                        target_hash=$(grep $component target_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | cut -d. -f1 |  sed 's/git//g'); echo $target_hash
                                elif [ $component == eos-csm_agent ]; then
                                        start_hash=$(grep $component start_build_manifest.txt | head -1 | awk -F['_'] '{print $3}' |  cut -d. -f1); echo $start_hash
                                        target_hash=$(grep $component target_build_manifest.txt | head -1 | awk -F['_'] '{print $3}' |  cut -d. -f1); echo $target_hash
                                else
                                        start_hash=$(grep $component start_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | sed 's/git//g'); echo $start_hash
                                        target_hash=$(grep $component target_build_manifest.txt | head -1 | awk -F['_'] '{print $2}' | sed 's/git//g'); echo $target_hash
                fi

                 pushd $dir
         echo -e "\t--[ Check-ins for $dir from $START_BUILD to $TARGET_BUILD ]--" >> $report_file
         echo -e "Githash|Description|Author|" >> $report_file
         git log $start_hash..$target_hash --oneline --pretty=format:"%h|%cd|%s|%an|" >>  $report_file
         echo -e "\n" >> $report_file
         echo -e "---------------------------------------------------------------------------------------------" >> $report_file
         popd
done
popd


echo "Printing report"
cat $clone_dir/clone/git-build-checkin-report.txt

