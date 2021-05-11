# Mini Provisioning / SSPL

## Purpose
 This ansible role used to perform sspl mini-provisioning on provided VM

## Wiki 
- https://github.com/Seagate/cortx-monitor/wiki/LR2:-SSPL-Self-Provisioning

## SSPL Role Structure

 ```

sspl
├── tasks
│   └── main.yml
└── vars
    └── config.yml
```

### 'tasks'

- main.yml
    - Performs deployment steps described in the [sspl mini-provisioner wiki](https://github.com/Seagate/cortx-monitor/wiki/LR2:-SSPL-Self-Provisioning)

### 'vars'
- config.yml
    - Holds role specific config