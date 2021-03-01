# OVA file generation

## Description
Generate OVA (Open Virtual Appliance) file from user mentioned CORTX build using ansible playbook.
This playbook consists variety of roles required to generate and test OVA as follow,

### Roles

  - vm-snapshot-revert : Revert single node cluster VM to base snapshot (undo all previous installations) 

  - vm-ssh-setup : Setup SSH connection between ansible deployment server and single node cluster VM 

  - vm-provisioner : Setup/Install cortx cluster on single node cluster VM 

  - vm-ovabuild : Create OVA file from single node cluster VM

  - vm-create : Create a new test VM from generated OVA

  - ova-tester : Run basic testcases on new test VM to ensure CORTX cluster availability
  
## How to generate OVA

Refer below jenkins job to create OVA

https://ssc-vm-0013.colo.seagate.com/job/EOS%20Open%20Source/job/ova-builder-testing/
  
:warning: Job is running on development jenkins instance. need to be updated for production
