#!/bin/bash
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

