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

SG_ADMIN_USR="$1"
SG_ADMIN_PWD="$2"

TEST_IDENTIFIER="$RANDOM"

# Install required tools to execute this test
_install_tools(){

    yum install python-pip expect -y
    pip install awscli
    pip install awscli-plugin-endpoint
}

# Create s3 test account using s3iamcli
_create_s3_account() {
    
    echo "------------ Create S3 Test Accounts -------------------------"
    ACC_ID="test_user_${TEST_IDENTIFIER}"
    ./create_s3_account.sh "$ACC_ID" "$ACC_ID@gmail.com" "${SG_ADMIN_USR}" "${SG_ADMIN_PWD}" >> "${ACC_ID}.log"
    S3_ACCESS_KEY=$(grep "AccountId" "${ACC_ID}.log" | cut -d, -f4 | cut -d= -f2  | tr -d '\r' |  xargs)
    S3_SECRET_KEY=$(grep "AccountId" "${ACC_ID}.log" | cut -d, -f5 | cut -d= -f2  | tr -d '\r' | xargs)
}

# configure s3 account for testig (s3 create/read/delete operations)
_configure_s3_account() {

    echo "------------ Configure S3 Test Accounts ----------------------"
    # Configure S3 endpoints
    aws configure set plugins.endpoint awscli_plugin_endpoint
    aws configure set s3.endpoint_url http://s3.seagate.com
    aws configure set s3api.endpoint_url http://s3.seagate.com

    # Configure S3 Account credentials
    aws configure set aws_access_key_id "${S3_ACCESS_KEY}"
    aws configure set aws_secret_access_key "${S3_SECRET_KEY}"
}

# Perform basic I/O test using s3cli
_test_s3_operations(){

    echo "------------ S3 Test Started ---------------------------------"

    BUCKET_NAME="seagate-test-${TEST_IDENTIFIER}"
    TEST_FILE="test_data_${TEST_IDENTIFIER}.txt"
   
    echo -e "1. Create S3 Bucket \n o/p: \n\t $(aws s3 mb s3://${BUCKET_NAME})"
    
    echo -e "2. List S3 Bucket  \n o/p: \n\t $(aws s3 ls)"

    touch "${TEST_FILE}"
    
    echo -e "3. Move data to S3 Bucket \n o/p: \n\t $(aws s3 mv ${TEST_FILE} s3://${BUCKET_NAME})"
    
    RESULT=$(aws s3 ls "s3://${BUCKET_NAME}")

    echo -e "4. List Bucket Content \n o/p: \n\t ${RESULT}"

    if [[ "${RESULT}" == *"${TEST_FILE}"* ]]; then
        echo "-----------> S3 Basic Testing Success <------------------"
    else
        echo "-----------> S3 Basic Testing Failed <--------------------"
        exit 1
    fi

    echo "------------ S3 Test Completed ---------------------------------"
}


_install_tools > /dev/null 2>&1

_create_s3_account 

_configure_s3_account

_test_s3_operations