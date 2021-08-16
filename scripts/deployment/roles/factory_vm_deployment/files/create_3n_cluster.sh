#!/bin/expect -f
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
# ./create_cluster.sh node1 node2 node3 pass build_url
spawn cortx_setup cluster create [lindex $argv 0] [lindex $argv 1] [lindex $argv 2] --name cortx_cluster --site_count 1 --storageset_count 1 --virtual_host [lindex $argv 3] --target_build [lindex $argv 4] 
set timeout 1200
expect {
    timeout {
        puts "Connection timed out"
        exit 1
    }

    -re "Enter root user password for.*" {
        send -- "[lindex $argv 5]\r"
        exp_continue
    }
}