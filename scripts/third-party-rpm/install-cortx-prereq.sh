#!/bin/bash

usage() { echo "Usage: $0 [ -b branch] [ -t third-party-version] [ -p python-deps-version] [ -o os-version ] [ -r RPM location]" 1>&2; exit 1; }

#Define Default values
BRANCH=main
OS_VERSION=centos-7.8.2003
THIRD_PARTY_VERSION=centos-7.8.2003-2.0.0-latest
PYTHON_DEPS_VERSION=python-packages-2.0.0-latest
RPM_LOCATION=remote

while getopts "t:p:b:o:r:" opt; do
    case $opt in
        t ) THIRD_PARTY_VERSION=$OPTARG;;
        p ) PYTHON_DEPS_VERSION=$OPTARG;;
        o ) OS_VERSION=$OPTARG;;
        b ) BRANCH=$OPTARG;;
        r ) RPM_LOCATION=$OPTARG;;
        h ) usage
        exit 0;;
        *) usage
        exit 1;;
    esac
done

echo " Using following values:"
echo "BRANCH $BRANCH"
echo "OS_VERSION $OS_VERSION"
echo "THIRD_PARTY_VERSION $THIRD_PARTY_VERSION"
echo "PYTHON_DEPS_VERSION $PYTHON_DEPS_VERSION"
echo "RPM_LOCATION $RPM_LOCATION"
echo ""

#Setup repositories and install packages
yum install yum-utils -y
yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/third-party-deps/centos/"$THIRD_PARTY_VERSION"/
yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/github/"$BRANCH"/"$OS_VERSION"/last_successful_prod/cortx_iso/
yum-config-manager --save --setopt=cortx-storage*.gpgcheck=1 cortx-storage* && yum-config-manager --save --setopt=cortx-storage*.gpgcheck=0 cortx-storage*

cat <<EOF >/etc/pip.conf
[global]
timeout: 60
index-url: http://cortx-storage.colo.seagate.com/releases/cortx/third-party-deps/python-deps/$PYTHON_DEPS_VERSION/
trusted-host: cortx-storage.colo.seagate.com
EOF

if [ "$RPM_LOCATION" == "remote" ]; then
    yum install java-1.8.0-openjdk-headless -y && yum install cortx-prereq -y
else
    yum install java-1.8.0-openjdk-headless -y && yum install /root/rpmbuild/RPMS/x86_64/*.rpm -y
fi

#Cleanup
rm -rf  /etc/yum.repos.d/cortx-storage.colo.seagate.com_releases_cortx_* /etc/pip.conf