#!/bin/bash

REPO="seagate/cortx"
ISO_LOCATION="/root/ISO"
RELEASE_REPO_LOCATION="/var/tmp/$RELEASE"
UPLOADS_REPO_LOCATION="/var/tmp/uploads"
RELEASE_REPO_FILE="$RELEASE.repo"


function _create_local_repo () {
        REPO_LOCATION=$1
        DOWNLOAD_RELEASE=$2
        ISO_DIR=$ISO_LOCATION/$(echo $REPO_LOCATION | awk -F'/' '{print $NF}')
        mount | grep $REPO_LOCATION && umount -f $REPO_LOCATION
        rm -rf $REPO_LOCATION
        mkdir $REPO_LOCATION
        mkdir -p $ISO_DIR && pushd $ISO_DIR
        githubrelease --github-token $GITHUB_TOKEN asset $REPO download $DOWNLOAD_RELEASE
        mount -o loop *.iso $REPO_LOCATION || exit
        popd
}

function _create_local_repo_file () {
rm -rf $RELEASE_REPO_FILE
cat << EOF >> $RELEASE_REPO_FILE
[releases_$RELEASE]
name=Cortx $RELEASE  Repository
baseurl=file://$RELEASE_REPO_LOCATION
gpgkey=file://$RELEASE_REPO_LOCATION/RPM-GPG-KEY-Seagate
gpgcheck=1
enabled=1

[uploads]
name=Cortx Uploads Repository
baseurl=file://$UPLOADS_REPO_LOCATION
gpgcheck=0
enabled=1
EOF
}

function _setup_local_repo () {
cp -f $RELEASE_REPO_FILE /etc/yum.repos.d/
yum clean all; rm -rf /var/cache/yum
}


_create_local_repo $RELEASE_REPO_LOCATION $RELEASE
_create_local_repo $UPLOADS_REPO_LOCATION $UPLOADS
_create_local_repo_file
_setup_local_repo
