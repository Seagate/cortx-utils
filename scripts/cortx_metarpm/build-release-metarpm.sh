#!/bin/bash

release_folder=$1
os_version=$2
build_num=$3
release_type="cortx"
build_location="http://cortx-storage.colo.seagate.com/releases/cortx/github/$release_folder/$os_version/$build_num/prod"

if [ -z "$release_folder" ] && [ -z "$os_version" ] && [ -z "$build_num" ]; then
   echo "Usage: build-release-metarpm.sh <release folder> <OS name> <release build number>"
   echo "e.g. build-release-metarpm.sh cortx-1.0 centos-7.7.1908 3"
   exit 1
fi

metainfo=$(curl "$build_location/" | sed -n "/rpm/p" | cut -d'"' -f 2 | tr ' ' '\n')
rpm --import "$build_location/RPM-GPG-KEY-Seagate"
rm -rf dependencies.txt

for i in $metainfo
do
rpm_name=$(rpm -qp "$build_location/$i" --qf '%{NAME}')
rpm_version=$(rpm -qp "$build_location/$i" --qf '%{VERSION}')
rpm_release=$(rpm -qp "$build_location/$i" --qf '%{RELEASE}')
echo "$rpm_name" = "$rpm_version"-"$rpm_release" >> dependencies.txt
done

builddep=$( < dependencies.txt tr '\n' ' ')
sed -i "s/release-name/$release_type/g" cortx.spec
sed -i "s/builddep/$builddep/g" cortx.spec
relversion=$build_num
sed -i "s/build-number/$relversion/" cortx.spec
rpmbuild -bb cortx.spec
