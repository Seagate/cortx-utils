# Docker images for CORTX CI

This document explains Docker image creating steps used in CORTX CI process.

## Docker Image generation

We use two Docker images in CORTX CI process. 

cortx-build-io:[os type]  - This is used for build IO stack components. Motr, S3server, Hare and NFS

cortx-build-cp:[os type]  - This is used for build control path stack components. Provisioner, cortx-management-portal, cortx-manager, cortx-monitor etc. 

## Steps to build Docker Images

```
$ git clone https://github.com/Seagate/cortx-re 
```
Got to OS specific driectory e.g centos-7.8.2003

```
$ cd $PWD/cortx-re/docker/internal-ci/centos-7.8.2003
```
Build cortx-build-cp image
```
$ docker build --target base --build-arg CENTOS_RELEASE=7.7.1908 --build-arg LUSTRE_VERSION=2.12.3 -t cortx-build-cp:centos-7.7.1908 .
$ docker tag cortx-build-cp:centos-7.8.2003 ssc-vm-0279.colo.seagate.com:5000/cortx-build-cp:centos-7.8.2003
$ docker push ssc-vm-0279.colo.seagate.com:5000/cortx-build-cp:centos-7.8.2003
```
Build cortx-build-io: image
```
$ docker build --build-arg CENTOS_RELEASE=7.8.2003 --build-arg LUSTRE_VERSION=2.12.5 -t cortx-build-io:centos-7.8.2003 
$ docker tag cortx-build-io:centos-7.8.2003 ssc-vm-0279.colo.seagate.com:5000/cortx-build-io:centos-7.8.2003
$ docker push ssc-vm-0279.colo.seagate.com:5000/cortx-build-io:centos-7.8.2003
```
