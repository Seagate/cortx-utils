#!/bin/bash
# Used for Manual Teardown. Currently not in use
# Referenece Document - https://seagate-systems.atlassian.net/wiki/spaces/PUB/pages/344556369/CORTX%2BTeardown%2BNode%2Bs
 
MOUNT_ENDPOINT=$(mount -l | grep gluster | cut -d ' ' -f3)
[[ -n "${MOUNT_ENDPOINT"} ]] && umount "${MOUNT_ENDPOINT"}

# Wipe the MBR of metadata volume
for vggroup in $(vgdisplay | egrep "vg_srvnode-"|tr -s ' '|cut -d' ' -f 4); do
    echo "Removing volume group ${vggroup}"
    vgremove --force "${vggroup}"
done
partprobe

device_list=$(lsblk -nd -o NAME -e 11|grep -v sda|sed 's|sd|/dev/sd|g'|paste -s -d, -)
for device in "${device_list}"
do
    wipefs --all "${device}"
done