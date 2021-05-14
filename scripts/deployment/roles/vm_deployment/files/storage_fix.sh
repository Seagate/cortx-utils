#!/bin/bash
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

salt "*" state.apply components.system.storage.teardown &>/dev/null || true

swapoff -a
for vggroup in $(vgdisplay | grep vg_metadata_srvnode-|tr -s ' '|cut -d' ' -f 4); do
    echo "Removing volume group ${vggroup}"
    vgremove --force "${vggroup}"
done

partprobe
for partition in $( ls -1 /dev/disk/by-id/scsi-*|grep part1 | rev | cut -c7- | rev ); do
    if parted "${partition}" print; then 
        echo "Removing partition 2 from ${partition}"
        echo "Ignore" | parted "${partition}" rm 2
    fi
done
partprobe

echo "cleanup command executed !!!"