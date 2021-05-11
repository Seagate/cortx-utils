# Mini Provisioning / Prepare Environment

## Purpose
 This ansible role used to perform prereq operation required for mini-provisioning through ansible. i.e enabling pasworless ssh between node, reimaging the vm for clean environment..etc 
 
## 00_prepare_environment Role Structure

 ```
00_prepare_environment/
├── files       
│   ├── passwordless_ssh.sh 
│   ├── reimage.sh
│   └── update_hosts.sh
└── tasks
    ├── 01_prepare_env.yml
    ├── 02_reimage.yml
    ├── main.yml
    └── passwordless_authentication.yml
```

### 'files'

- passwordless_ssh.sh 
    - Used to enable passwordless ssh between deployment node and execution machine
- reimage.sh
     - Used to reimage the provided clodform VM (internal seagate cloudform account)
- update_hosts.sh
     - Dynamically update ansible host file based on HOST argument

### 'tasks'

- main.yml
    - Act as a entry point for role execution
- 01_prepare_env.yml
    - Install tools required for deployment activity
    - Updates host for ansible node communication
    - Enabled passwordless ssh between deployment node and execution machine
- 02_reimage.yml
    - Reimage the provided clodform VM and validates the host health
- passwordless_authentication.yml
    - Genric task that enabled passwordless ssh, can be reused in the required places

