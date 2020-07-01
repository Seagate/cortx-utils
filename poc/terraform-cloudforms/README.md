# Terraform - Cloudforms VM Provisoning

This terraform configuration uses [terraform-provider-cloudforms](https://github.com/GSLabDev/terraform-provider-cloudforms) for cloudform VM provisioning.


## Requirements

* Cloudfrom username/password
* Terraform should be installed

## Providers

| Name | Version |
|------|---------|
| cloudforms | n/a |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| CF\_PASSWORD | cloudforms user password | `string` | n/a | yes |
| CF\_SERVER\_IP | cloudforms host/ip | `string` | n/a | yes |
| CF\_USER\_NAME | cloudforms username | `string` | n/a | yes |
| SERVICE\_NAME | service name (RHEL,CENTOS,UBUNTU) | `string` | n/a | yes |
| SERVICE\_TEMPLATE\_NAME | service name template ( 2x RHEL7.7, RHEL7.7..etc) | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| service\_catalog\_id | service catalog id for refernce |
| service\_name | service name id for refernce |
| service\_request | service request id (order id) |
| service\_template\_href |service template href for reference|


## Note

* [terraform-provider-cloudforms](https://github.com/GSLabDev/terraform-provider-cloudforms) is pre-build and added in the plugin dir (``.terraform/plugins/linux_amd64``)