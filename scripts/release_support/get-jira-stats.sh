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

REPORT_DIR="/root/jira/"
REPORT_FILE="jira-stats.txt"
OUTPUT_JSON="$REPORT_DIR/output.json"
COMPONENT_LIST=(Provisioner CSM hare Mero S3Server RAS)
#COMPONENT_LIST=(Provisioner hare)

rm -rf $REPORT_DIR
mkdir -p $REPORT_DIR
for component in  "${COMPONENT_LIST[@]}"

do
echo -e "\nJira stats for $component at $(date) for last 12 Hours" >> $REPORT_DIR/$REPORT_FILE
sed -i 's/component_name/'$component'/' input.json
curl -s -X POST  -u ${JIRA_PASS}  -H "Content-Type: application/json"  -d @input.json  https://jts.seagate.com/rest/api/2/search -o $OUTPUT_JSON

n=`jq .issues[] $OUTPUT_JSON | grep "expand" | wc -l`
for (( i=0; i<$n; i++ ))
do
echo `jq .issues[$i].key $OUTPUT_JSON && jq .issues[$i].fields.assignee.displayName $OUTPUT_JSON && jq .issues[$i].fields.summary $OUTPUT_JSON && jq .issues[$i].fields.status.name $OUTPUT_JSON` >> $REPORT_DIR/$REPORT_FILE
done
sed -i 's/'$component'/component_name/' input.json
done

cat $REPORT_DIR/$REPORT_FILE
