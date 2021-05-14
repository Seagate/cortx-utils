# Mini Provisioning / Prepare Environment

## Purpose
 This ansible role used to perform prereq operation required for mini-provisioning through ansible. i.e enabling pasworless ssh between node, reimaging the vm for clean environment..etc 
 
## 00_prepare_environment Role Structure

 ```
00_prepare_environment/
├── files       
│   ├── passwordless_ssh.sh 
│   └── update_hosts.sh
└── tasks
    └── main.yml
```

### 'files'

- passwordless_ssh.sh 
    - Used to enable passwordless ssh between deployment node and execution machine
- update_hosts.sh
     - Dynamically update ansible host file based on HOST argument

### 'tasks'

- main.yml
    - Install tools required for deployment activity
    - Updates host for ansible node communication
    - Enabled passwordless ssh between deployment node and execution machine

