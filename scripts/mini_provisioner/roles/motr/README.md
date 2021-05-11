# Mini Provisioning / Motr

## Purpose
 This ansible role used to perform motr mini-provisioning on provided VM
 
## Wiki 
- https://github.com/Seagate/cortx-motr/wiki/Motr-deployment-using-motr_setup-on-singlenode-VM

## Motr Role Structure

 ```
motr
├── files
│   ├── reset_machineid.sh
│   └── run_io_tests.sh
├── tasks
│   ├── 01_install_prerequisites.yml
│   ├── 02_mini_provisioning.yml
│   ├── 03_bootstrap_cluster.yml
│   ├── 04_validate.yml
│   └── main.yml
├── templates
│   ├── confstore.json.j2
│   ├── cortx.repo.j2
│   └── singlenode.yml.j2
└── vars
    └── config.yml

```

### 'files'

- reset_machineid
    - This is used to reset vm machine-id
- run_io_tests.sh
    - Validates Motr deployment by performing IO 

### 'tasks'

- main.yml
    - Acts as a entry point for role execution
- 01_install_prerequisites.yml
    - Performs prereq steps described in the motr wiki
- 02_mini_provisioning.yml
    - Performs mini-provisioning steps described in the motr wiki
- 03_bootstrap_cluster.yml
    - Starts motr cluster
- 04_validate.yml
    - Performs IO to validate the deployment

### 'template'

- confstore.json.j2
    - Cortx deployment configuration file with required motr configurations 
- cortx.repo.j2
    - Constructs yum repo required for deployment, i.e cortx-rpm, 3rd-party and uploads
- singlenode.yml.j2
    - Cluster definition file used for cluster bootstrapping

### 'vars'
- config.yml
    - Holds role specific config