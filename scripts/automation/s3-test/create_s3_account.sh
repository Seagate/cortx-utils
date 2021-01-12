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
# ./create_s3_account.sh username email ldap_user ldap_pwd

set USER_NAME [lindex $argv 0];
set USER_EMAIL [lindex $argv 1];
set LDAP_USER [lindex $argv 2];
set LDAP_PWD [lindex $argv 3];

spawn s3iamcli CreateAccount -n $USER_NAME -e $USER_EMAIL
set timeout 20
expect {
    timeout {
        puts "Connection timed out"
        exit 1
    }

    "Ldap User Id:" {
        send "$LDAP_USER\r"
        exp_continue
    }

    "Ldap password:" {
        send -- "$LDAP_PWD\r"
        exp_continue
    }
}