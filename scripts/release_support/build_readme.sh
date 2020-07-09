#/bin/bash
BUILD_LOCATION=$1
echo -e "Generating README.txt file"
pushd $BUILD_LOCATION
cat <<EOF > README.txt
CONTENTS OF THIS FILE
---------------------

 * Introduction
 * Artifacts
 * Provisioner Guide
 * Known Issues


Introduction
------------

EES Details to be added here.


Artifacts
------------
Release Build location:

http://ci-storage.mero.colo.seagate.com/releases/eos/github/master/rhel-7.7.1908/$ENV/$BUILD_NUMBER/

Release Info file location:

http://ci-storage.mero.colo.seagate.com/releases/eos/github/master/rhel-7.7.1908/$ENV/$BUILD_NUMBER/RELEASE.INFO

Installation
-----------------

Provisioner Guide

http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr/wikis/Setup-Guides/QuickStart-Guide


Known Issues
------------

Known issues are tracked at

http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr/wikis/Known-issues-for-deploy-eos
EOF

