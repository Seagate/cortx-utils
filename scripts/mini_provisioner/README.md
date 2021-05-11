# Cortx Mini-Provisioning

## Purpose
 This playbook acts as a wrapper for cortx component mini-provisioning and provides flexibility to deploy & validate the specific component on a single click.
 
## Cortx components
 - [cortx-motr](roles/motr/README.md)
 - [cortx-s3server](roles/s3server/README.md)
 - [cortx-hare](roles/hare/README.md)
 - [cortx-monitor](roles/sspl/README.md)
 - [cortx-manager](roles/csm/README.md)
 - [cortx-utils](roles/pyutils/README.md)
 
 ## What it Does

- Perform prereq for deployment
    - Enabling passwordless SSH between deploy node and executor machine
- Executes deployment steps provided in the component mini-provisioning wiki


## How it works

This deployment wrapper was developed in ansible. so calling ansible playbook with required deployment parameters will start the deployment process.


### Prerequisite

Install Ansible on the execution host
```
yum install -y ansible
```

Clone cortx-re repo and navigate to mini-provisioner folder
```
    git clone https://github.com/Seagate/cortx-re -b main
    cd cortx-re/scripts/mini_provisioner
```

#### Motr deployment
``` 
    ansible-playbook motr_deploy.yml --extra-vars "NODE1=<CLEAN_VM_FQDN> CORTX_BUILD=<CORXT_BUILD_HTTP_URL>"
```

#### S3server deployment
``` 
    ansible-playbook s3server_deploy.yml --extra-vars "NODE1=<CLEAN_VM_FQDN> CORTX_BUILD=<CORXT_BUILD_HTTP_URL>" 
```

#### Hare deployment
``` 
    ansible-playbook hare_deploy.yml --extra-vars "NODE1=<CLEAN_VM_FQDN> CORTX_BUILD=<CORXT_BUILD_HTTP_URL>" 
```

#### Monitor deployment
``` 
    ansible-playbook sspl_deploy.yml --extra-vars "NODE1=<CLEAN_VM_FQDN> CORTX_BUILD=<CORXT_BUILD_HTTP_URL>" 
```

#### Manager deployment
``` 
    ansible-playbook csm_deploy.yml --extra-vars "NODE1=<CLEAN_VM_FQDN> CORTX_BUILD=<CORXT_BUILD_HTTP_URL>" 
```

#### PyUtils deployment
``` 
    ansible-playbook pyutils_deploy.yml --extra-vars "NODE1=<CLEAN_VM_FQDN> CORTX_BUILD=<CORXT_BUILD_HTTP_URL>" 
```


#### Directory Structure

```
│   ansible.cfg
│   csm_deploy.yml
│   hare_deploy.yml
│   host_cleanup.yml
│   motr_deploy.yml
│   prepare.yml
│   provisioner_deploy.yml
│   pyutils_deploy.yml
│   README.md
│   s3server_deploy.yml
│   sspl_deploy.yml
│
├───inventories
│       hosts
│
└───roles
    ├───00_prepare_environment
    │   │   README.md
    │   │
    │   ├───files
    │   │       passwordless_ssh.sh
    │   │       reimage.sh
    │   │       update_hosts.sh
    │   │
    │   └───tasks
    │           01_prepare_env.yml
    │           02_reimage.yml
    │           main.yml
    │           passwordless_authentication.yml
    │
    ├───csm
    │   │   README.md
    │   │
    │   ├───tasks
    │   │       01_install_prerequisites.yml
    │   │       02_mini_provisioning.yml
    │   │       03_start_csm.yml
    │   │       04_validate.yml
    │   │       main.yml
    │   │
    │   ├───templates
    │   │       cortx.repo.j2
    │   │       utils_config.j2
    │   │
    │   └───vars
    │           config.yml
    │
    ├───ha
    │   │   README.md
    │   │
    │   ├───tasks
    │   │       main.yml
    │   │
    │   ├───templates
    │   │       confstore.json.j2
    │   │       cortx.repo.j2
    │   │
    │   └───vars
    │           config.yml
    │
    ├───hare
    │   │   README.md
    │   │
    │   ├───files
    │   │       lnet.conf
    │   │
    │   ├───tasks
    │   │       01_install_prerequisites.yml
    │   │       02_mini_provisioning.yml
    │   │       04_validate.yml
    │   │       main.yml
    │   │
    │   ├───templates
    │   │       cortx.repo.j2
    │   │
    │   └───vars
    │           config.yml
    │
    ├───host_cleanup
    │   ├───tasks
    │   │       01_cleanup_cortx_stack.yml
    │   │       main.yml
    │   │
    │   └───vars
    │           config.yml
    │
    ├───motr
    │   │   README.md
    │   │
    │   ├───files
    │   │       reset_machineid.sh
    │   │       run_io_tests.sh
    │   │
    │   ├───tasks
    │   │       01_install_prerequisites.yml
    │   │       02_mini_provisioning.yml
    │   │       03_bootstrap_cluster..yml
    │   │       04_validate.yml
    │   │       main.yml
    │   │
    │   ├───templates
    │   │       cortx.repo.j2
    │   │       singlenode.yml.j2
    │   │
    │   └───vars
    │           config.yml
    │
    ├───provisioner
    │   │   README.md
    │   │
    │   ├───files
    │   │       setup_provisioner.sh
    │   │
    │   ├───tasks
    │   │       01_deploy_prereq.yml
    │   │       02_deploy.yml
    │   │       03_platform_setup.yml
    │   │       main.yml
    │   │
    │   ├───templates
    │   │       config.ini.j2
    │   │
    │   └───vars
    │           config.yml
    │
    ├───pyutils
    │   │   README.md
    │   │
    │   ├───files
    │   │       install_kafka.sh
    │   │
    │   ├───tasks
    │   │       01_install_prerequisites.yml
    │   │       02_mini_provisioning.yml
    │   │       04_validate.yml
    │   │       main.yml
    │   │
    │   ├───templates
    │   │       cortx.repo.j2
    │   │
    │   └───vars
    │           config.yml
    │
    ├───s3server
    │   │   README.md
    │   │
    │   ├───files
    │   │       lnet.conf
    │   │       start_service.sh
    │   │       test_s3server.sh
    │   │
    │   ├───tasks
    │   │       01_install_prerequisites.yml
    │   │       02_mini_provisioning.yml
    │   │       03_start_s3server.yml
    │   │       04_validate.yml
    │   │       main.yml
    │   │
    │   ├───templates
    │   │       cortx.repo.j2
    │   │       singlenode.yml.j2
    │   │       utils_confstore.json.j2
    │   │
    │   └───vars
    │           config.yml
    │
    └───sspl
        │   README.md
        │
        ├───tasks
        │       01_install_prerequisites.yml
        │       02_mini_provisioning.yml
        │       03_start_sspl.yml
        │       04_validate.yml
        │       main.yml
        │
        ├───templates
        │       cortx.repo.j2
        │       utils_config.j2
        │
        └───vars
                config.yml
```