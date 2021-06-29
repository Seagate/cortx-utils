#!/bin/bash


#Install Terraform
echo -e "-------------------------[ Installing Terraform ]----------------------------------------" 
yum install -y yum-utils
yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
yum -y install terraform


#Install AWS CLI
echo -e "-------------------------[ Installing  AWS CLI   ]----------------------------------------" 
mkdir -p /opt/aws-cli/
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/opt/aws-cli/awscliv2.zip"
unzip "/opt/aws-cli/awscliv2.zip" -d /opt/aws-cli/
sudo /opt/aws-cli/aws/install
rm -rf /opt/aws-cli/aws

#Trigger AWS CLI configuration
echo -e "-------------------------[ AWS CLI configuration ]----------------------------------------" 
aws configure


#Initiate Terraform workspace
echo -e "------------------------[ Terraform Workspace init ]----------------------------------------" 
terraform init

