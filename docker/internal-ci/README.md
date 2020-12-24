# Docker images for CORTX CI

This document explains Docker image creating steps used in CORTX CI process.

## Docker Image generation

We use two Docker images in CORTX CI process. 

- cortx-build-io:[os type]  - This is used for build IO stack components. Motr, S3server, Hare and NFS

- cortx-build-cp:[os type]  - This is used for build control path stack components. Provisioner, cortx-management-portal, cortx-manager, cortx-monitor etc. 

## Steps to build Docker Images

- Install docker on your system. Refer https://docs.docker.com/engine/install/centos/ 

- Install docker-compose on your system. Refer https://docs.docker.com/compose/install/

- Clone cortx-re repository.

```
$ git clone https://github.com/Seagate/cortx-re 
```

- Change directory to internal-ci

```
$ cd $PWD/cortx-re/docker/internal-ci/
```
- Build images using below command.

```
$ docker-compose build
```

- To build specific image provide image details to command. e.g. For `cortx-build-io:centos-7.8.2003` image use below command.
```
$ docker-compose build cortx-build-io-centos-7.8.2003
```