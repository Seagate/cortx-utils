#!/bin/bash

#Only root to should run setup
if [ $(whoami) != root ];then
	echo "$(whoami) is not root user. Please use root user to execute this script"
	exit
fi

#Configure Elastic Network cards
echo "Configuring Elastic NIC"
for nic in eth1 eth2
do
   MAC=$(ifconfig $nic | grep -o -E '([[:xdigit:]]{2}:){5}[[:xdigit:]]{2}')
   cp /etc/sysconfig/network-scripts/ifcfg-eth0 /etc/sysconfig/network-scripts/ifcfg-$nic
   sed -i 's/eth0/$nic/g' /etc/sysconfig/network-scripts/ifcfg-$nic
   sed -i -e '/HWADDR/d' /etc/sysconfig/network-scripts/ifcfg-$nic
   sed -i "5 a HWADDR=$MAC" /etc/sysconfig/network-scripts/ifcfg-$nic
   echo -e "SUBSYSTEM==\"net\", ACTION==\"add\", DRIVERS==\"?*\", ATTR{address}==\"$MAC\", NAME=\"$nic\"" >> /etc/udev/rules.d/70-persistent-net.rules
done

echo "GATEWAYDEV=eth0" >> /etc/sysconfig/network
echo "Restarting Network Service"
systemctl restart network

echo "All networks should have ip address assigned" 
/sbin/ip a 

#Setup udev rules for ESB volumes. Refer- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html#ec2-nitro-instances 
echo "Mapping Nitro EBS volumes"
declare -a device_list
readarray -t device_list < <(lsblk -o NAME | grep -E -v 'nvme0n1|\NAME')
mapping=(sdb sdc sdd sde sdf sdg sdh sdi sdj)

for ((i = 0; i < ${#device_list[@]}; i++)); do
   echo KERNEL==\""${device_list[$i]}"\", SUBSYSTEM==\"block\", SYMLINK=\""${mapping[$i]}"\" >> /etc/udev/rules.d/99-custom-dev.rules
done
echo "Rebooting system....."
#System reboot
reboot
