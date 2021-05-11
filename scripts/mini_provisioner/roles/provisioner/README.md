# Mini Provisioning / Provisioner

## Purpose
 This ansible role used to perform provisioner mini-provisioning on provided VM 
 
## Wiki 
- https://github.com/Seagate/cortx-prvsnr/wiki/Auto-Deploy-VM-Provisioner-CLI-Commands 

## Provisioner Role Structure

```
provisioner/
├── files
│   └── setup_provisioner.sh
├── tasks
│   ├── 01_deploy_prereq.yml
│   ├── 02_deploy.yml
│   ├── 03_platform_setup.yml
│   └── main.yml
├── templates
│   └── config.ini.j2
└── vars
    └── config.yml
```

### 'files'

- setup_provisioner.sh
    - Installs provisioner api and bootstrap provisioner VM 

### 'tasks'

- main.yml
    -  Acts as a entry point for role execution
- 01_deploy_prereq.yml
    - Install dependencies and setup config file 
- 02_deploy.yml
    - Deploy single node cluster and validate services 
- 03_platform_setup.yml
    - Setup platform and 3rd party software deployment

### 'template'

- config.ini.j2
    - Configuration file with required provisioner configurations

### 'vars'
- config.yml
    - Used for playbook config declarations
