#!/usr/bin/python

import subprocess

dev_list = subprocess.Popen(["multipath -ll|grep mpath |sort -k2|cut -d' ' -f1|sed 's|mpath|/dev/disk/by-id/dm-name-mpath|g'"], shell=True, stdout=subprocess.PIPE).stdout
split_dev = dev_list.read().splitlines()
length = len(split_dev)
middle_index = length//2
first_half = split_dev[:middle_index]
cvg0_data_list = first_half[0:7]
cvg0_data_dev = ",".join(cvg0_data_list)
print(cvg0_data_dev)
