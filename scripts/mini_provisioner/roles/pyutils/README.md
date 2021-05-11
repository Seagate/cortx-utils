# Mini Provisioning / PyUtils

## Purpose
 This ansible role used to perform pyutils mini-provisioning on provided VM

## Wiki 
- https://github.com/Seagate/cortx-utils/wiki/%22cortx-py-utils%22-single-node-manual-provisioning
 
## Motr PyUtils Structure

 ```
pyutils/
├── files
│   └── install_kafka.sh
├── tasks
│   └── main.yml
├── templates
│   ├── confstore.json.j2
│   └── cortx.repo.j2
└── vars
    └── config.yml

```

### 'files'

- install_kafka.sh
    - Installs kafka on vm and starts it in background

### 'tasks'

- main.yml
    - Performs deployment steps described in the [pyutils mini-provisioner wiki](https://github.com/Seagate/cortx-utils/wiki/%22cortx-py-utils%22-single-node-manual-provisioning)

### 'template'

- confstore.json.j2
    - Cortx deployment configuration file with required pyutils configurations 
- cortx.repo.j2
    - Constructs yum repo required for deployment, i.e cortx-rpm

### 'vars'
- config.yml
    - Holds role specific config