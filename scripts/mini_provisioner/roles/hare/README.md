# Mini Provisioning / Hare

## Purpose
 This ansible role used to perform hare mini-provisioning on provided VM 
 
## Wiki 
- https://github.com/Seagate/cortx-hare/wiki/Hare-provisioning

## Hare Role Structure

 ```
hare
├── files
│   └── lnet.conf
├── tasks
│   ├── 01_install_prerequisites.yml
│   ├── 02_mini_provisioning.yml
│   └── main.yml
├── templates
│   ├── confstore.json.j2
│   └── cortx.repo.j2
└── vars
    └── config.yml

```

### 'files'

- lnet.conf
    - This is needed for motr deployment (hare deployment dependency)

### 'tasks'

- main.yml
    -  Acts as a entry point for role execution
- 01_install_prerequisites.yml
    - Performs prereq steps described in the [hare wiki](https://github.com/Seagate/cortx-hare/wiki/Hare-provisioning#pre-requisites)
- 02_mini_provisioning.yml
    - Performs mini-provisioning steps as per [hare wiki](https://github.com/Seagate/cortx-hare/wiki/Hare-provisioning#provisioning)

### 'template'

- confstore.json.j2
    - Cortx deployment configuration file with required hare configurations 
- cortx.repo.j2
    - Constructs yum repo required for deployment, i.e cortx-rpm, uploads

### 'vars'
- config.yml
    - Used for playbook config declarations