variable "security_group_cidr" {
  description = "Value of CIDR block to be used for Security Group. This should be your systems public-ip"
  type        = string
}

variable "region" {
  description = "Region"
  type        = string
}

variable "key_name" {
  description = "SSH Key name"
  type        = string
  default     = "cortx-key"
}

