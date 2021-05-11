# Mini Provisioning / CSM

## Purpose
This ansible role used to perform csm mini-provisioning on provided VM

## Wiki 
- https://github.com/Seagate/cortx-manager/wiki/CORTX-Manager-Single-Node-Deployment-on-VM-:-Manual

## CSM Role Structure

 ```
csm
├── tasks
│   └── main.yml
├── templates
│   └── cortx.repo.j2
└── vars
    └── config.yml
```

### 'tasks'

- main.yml
    - Performs steps described in the [csm mini-provisioning wiki](https://github.com/Seagate/cortx-manager/wiki/CORTX-Manager-Single-Node-Deployment-on-VM-:-Manual)


### 'templates'

- cortx.repo.j2
    - Constructs yum repo required for deployment, i.e cortx-rpm, uploads

### 'vars'
- config.yml
    - Used for required parameter declaration