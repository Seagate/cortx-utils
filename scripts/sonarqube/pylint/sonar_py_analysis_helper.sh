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

#####################################################################################################################################
# Purpose:
#       Sonarqube does not contain rule for 'Copyright header check' for python file. This script does the copyright header check
# for python files and generates the json file in the format of Sonarqube Generic Issue Data
#
#       Ref : https://docs.sonarqube.org/latest/analysis/generic-issue/ 
#
####################################################################################################################################


# Get all files with no seagate copyright header
NO_COPYRIGHT_HEADER_PY=($(grep -rL "COPYRIGHT.*SEAGATE LLC" --include=*.py .))

# Sonarqube 'Generic Issue Data' Template
EXTERNAL_ISSUE_DATA_SONNAR='{"engineId":"Track lack of copyright and license headers","ruleId":"py:copyrightHeader","severity":"BLOCKER","type":"CODE_SMELL","primaryLocation":{"message":"Add or update the copyright header of this file","filePath":"%s","textRange":{"startLine":1,"endLine":2}}},'

# Result File
RESULT_FILE="sonarqube_external_issues.json"

#Logic to generate the Json with 'Generic Issue Data' content
printf '{"issues":[' >> ${RESULT_FILE}
for FILE_NAME in "${NO_COPYRIGHT_HEADER_PY[@]}"
do
    printf "$EXTERNAL_ISSUE_DATA_SONNAR" "${FILE_NAME}" >> ${RESULT_FILE}
done
sed -i '$ s/.$//' ${RESULT_FILE}
printf ']}' >> ${RESULT_FILE}

echo "Successfully generated the json file with the sonarqube issue data"