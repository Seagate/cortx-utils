# Variables Declaration
#####################################################################
variable "CF_SERVER_IP" {
  type = string
}

variable "CF_USER_NAME" {
  type = string
}

variable "CF_PASSWORD" {
  type = string
}

variable "SERVICE_NAME" {
  type = string
}

variable "SERVICE_TEMPLATE_NAME" {
  type = string
}

# Cloudform Provider initialization
#######################################################################
provider "cloudforms" {
	ip = var.CF_SERVER_IP
	user_name = var.CF_USER_NAME
	password = var.CF_PASSWORD
}


# Terraform resource operations
#######################################################################

# Data Source cloudforms_service
data  "cloudforms_service" "main"{
    name = var.SERVICE_NAME
}

# Data Source cloudforms_service_template
data "cloudforms_service_template" "main"{
	name = var.SERVICE_TEMPLATE_NAME
}


# Resource 'cloudforms_service_request' to create cloudform vm
resource "cloudforms_service_request" "main" {	
 	name = "terraform-created-vm"
 	template_href = data.cloudforms_service_template.main.href
 	catalog_id = data.cloudforms_service_template.main.service_template_catalog_id
 	input_file_name = "data.json"
 	time_out= 1800
}


# Output resource attributes for reference
#######################################################################
output "service_template_href" {
	value = data.cloudforms_service_template.main.href
}

output "service_name" {
	value = data.cloudforms_service.main.name
}

output "service_catalog_id" {
	value = data.cloudforms_service_template.main.service_template_catalog_id
}

output "service_request" {
	value = cloudforms_service_request.main
}
