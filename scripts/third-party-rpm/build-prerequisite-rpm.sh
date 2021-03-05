#!/bin/bash

set -e -o pipefail

usage() { echo "Usage: $0 [-v version] [-r release] [-g git-version]" 1>&2; exit 1; }

while getopts ":r:v:g:" o; do
    case "${o}" in
        v)
            VERSION=${OPTARG}
            ;;
        g)
            GIT_VERSION=${OPTARG}
            ;;
        r)
            RELEASE_VERSION=${OPTARG}
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${RELEASE_VERSION}" ] || [ -z "${VERSION}" ]; then
    usage
fi

if [ -z "${GIT_VERSION}" ]; then
GIT_VERSION=$(git rev-parse --short HEAD)
fi
DIST_DIR=cortx-prereq-$VERSION-git$GIT_VERSION

#Generate source tar
mkdir -p "$DIST_DIR"
cp -- *.txt  "$DIST_DIR"/
tar -cvzf /root/rpmbuild/SOURCES/"$DIST_DIR".tgz "$DIST_DIR"

#Add require packages
builddep=$(grep -v "#" third-party-rpms.txt |  tr '\n' ' ')
sed -i "s/third-party-deps/$builddep/g" cortx-prereq.spec

#Generate RPM
rpmbuild -bb cortx-prereq.spec --define "_cortx_prereq_version $VERSION" --define "_release_version $RELEASE_VERSION" --define "_git_hash git$GIT_VERSION"

rm -rf "$DIST_DIR"
