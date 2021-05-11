# Mini Provisioning / S3server

## Purpose
 This ansible role used to perform s3server mini-provisioning on provided VM
 
## Wiki 
- https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual

## S3server Role Structure

 ```
s3server
├── files
│   ├── lnet.conf
│   ├── install_configure_kafka.sh
├── tasks
│   ├── 01_install_prerequisites.yml
│   ├── 02_install_s3server.yml
│   ├── 03_mini_provisioning.yml
│   ├── 04_start_s3server.yml
│   └── main.yml
├── templates
│   ├── confstore.json.j2
│   ├── cortx.repo.j2
│   └── singlenode.yml.j2
└── vars
    └── config.yml
```

### 'files'

- lnet.conf
    - This is needed for s3server deployment (s3server deployment dependency)
- install_configure_kafka.sh
    -  Installs & configures kafka using script - s3server/script/kafka/

### 'tasks'

- main.yml
    - Act as a entry point for role execution
- 01_install_prerequisites.yml
    - Perform prereq steps described in the s3server wiki
- 02_install_s3server.yml
    - Installs s3server and dependent components
- 03_mini_provisioning.yml
    - Performs mini-provisioning steps described in the s3server wiki
- 04_start_s3server.yml
    - Starts s3server and bootstarp the cluster

### 'template'

- confstore.json.j2
    - Cortx deployment configuration file with required s3server configurations 
- cortx.repo.j2
    - Constructs yum repo required for deployment, i.e cortx-rpm, 3rd-party and uploads
- singlenode.yml.j2
    - Cluster definition file used for cluster bootstrapping

### 'vars'
- config.yml
    - Holds role specific config