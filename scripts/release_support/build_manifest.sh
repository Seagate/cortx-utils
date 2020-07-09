#/bin/bash
BUILD_LOCATION=$1
echo -e "Generating RELEASE.INFO file"
pushd $BUILD_LOCATION
cat <<EOF > RELEASE.INFO
---
NAME: "EES"
VERSION: "1.0.0"
BUILD: $(echo $BUILD_NUMBER | sed -e 's/^/\"/g' -e 's/$/\"/g')
OS: $(cat /etc/redhat-release | sed -e 's/ $//g' -e 's/^/\"/g' -e 's/$/\"/g')
DATETIME: $(date +"%d-%b-%Y %H:%M %Z" | sed -e 's/^/\"/g' -e 's/$/\"/g')
KERNEL: $(ls cortx-motr-[0-9]*.rpm | sed -e  's/.*3/3/g' -e 's/.x86_64.rpm//g' -e 's/^/\"/g' -e 's/$/\"/g')
LUSTRE_VERSION: $(ls lustre-*.src.rpm | sed -e 's/.src.rpm//g'  -e 's/^/\"/g' -e 's/$/\"/g')
COMPONENTS:
$(ls -1 *.rpm | awk '{ print "    - \""$1"\""}')
EOF
popd
