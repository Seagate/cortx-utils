# COPYRIGHT 2020 SEAGATE LLC
#
# THIS DRAWING/DOCUMENT, ITS SPECIFICATIONS, AND THE DATA CONTAINED
# HEREIN, ARE THE EXCLUSIVE PROPERTY OF SEAGATE TECHNOLOGY
# LIMITED, ISSUED IN STRICT CONFIDENCE AND SHALL NOT, WITHOUT
# THE PRIOR WRITTEN PERMISSION OF SEAGATE TECHNOLOGY LIMITED,
# BE REPRODUCED, COPIED, OR DISCLOSED TO A THIRD PARTY, OR
# USED FOR ANY PURPOSE WHATSOEVER, OR STORED IN A RETRIEVAL SYSTEM
# EXCEPT AS ALLOWED BY THE TERMS OF SEAGATE LICENSES AND AGREEMENTS.
#
# YOU SHOULD HAVE RECEIVED A COPY OF SEAGATE'S LICENSE ALONG WITH
# THIS RELEASE. IF NOT PLEASE CONTACT A SEAGATE REPRESENTATIVE
# http://www.seagate.com/contact
#
# Original author: Gowthaman Chinnathambi
# Original creation date: 27-03-2020

#!/bin/bash - 
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