#!/usr/bin/python

import subprocess

dev_list = subprocess.Popen(["multipath -ll|grep mpath |sort -k2|cut -d' ' -f1|sed 's|mpath|/dev/disk/by-id/dm-name-mpath|g'"], shell=True, stdout=subprocess.PIPE).stdout
split_dev = dev_list.read().splitlines()
length = len(split_dev)
middle_index = length//2
second_half = split_dev[middle_index:]
cvg1_data_list = second_half[0:7]
cvg1_data_dev = ",".join(cvg1_data_list)
print(cvg1_data_dev)
