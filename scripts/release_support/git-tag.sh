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

declare -A COMPONENT_LIST=(
                        [cortx-s3server]="https://$PASSWD@github.com/Seagate/cortx-s3server.git"
                        [cortx-motr]="https://$PASSWD@github.com/Seagate/cortx-motr.git"
                        [cortx-hare]="https://$PASSWD@github.com/Seagate/cortx-hare.git"
                        [cortx-ha]="https://$PASSWD@github.com/Seagate/cortx-ha.git"
                        [cortx-prvsnr]="https://$PASSWD@github.com/Seagate/cortx-prvsnr.git"
                        [cortx-sspl]="https://$PASSWD@github.com/Seagate/cortx-monitor.git"
                        [cortx-csm_agent]="https://$PASSWD@github.com/Seagate/cortx-manager.git"
                        [cortx-csm_web]="https://$PASSWD@github.com/Seagate/cortx-management-portal.git"
                        [cortx-py-utils]="https://$PASSWD@github.com/Seagate/cortx-utils.git"
                        [cortx-prereq]="https://$PASSWD@github.com/Seagate/cortx-re.git"
                )

declare -A REPO_LIST=(
                        [cortx-s3server]="https://$PASSWD@api.github.com/repos/Seagate/cortx-s3server/releases"
                        [cortx-motr]="https://$PASSWD@api.github.com/repos/Seagate/cortx-motr/releases"
                        [cortx-hare]="https://$PASSWD@api.github.com/repos/Seagate/cortx-hare/releases"
                        [cortx-ha]="https://$PASSWD@api.github.com/repos/Seagate/cortx-ha/releases"
                        [cortx-prvsnr]="https://$PASSWD@api.github.com/repos/Seagate/cortx-prvsnr/releases"
                        [cortx-sspl]="https://$PASSWD@api.github.com/repos/Seagate/cortx-monitor/releases"
                        [cortx-csm_agent]="https://$PASSWD@api.github.com/repos/Seagate/cortx-manager/releases"
                        [cortx-csm_web]="https://$PASSWD@api.github.com/repos/Seagate/cortx-management-portal/releases"
                        [cortx-py-utils]="https://$PASSWD@api.github.com/repos/Seagate/cortx-utils/releases"
                        [cortx-prereq]="https://$PASSWD@api.github.com/repos/Seagate/cortx-re/releases"
                )

                        git config --global user.email "cortx-application@seagate.com"
                        git config --global user.name "cortx-admin"
                        wget -q "$RELEASE_INFO_URL" -O RELEASE.INFO

        for component in "${!COMPONENT_LIST[@]}"

        do
                dir="$(echo "${COMPONENT_LIST[$component]}" |  awk -F'/' '{print $NF}')"
                git clone --quiet "${COMPONENT_LIST["$component"]}" "$dir" > /dev/null

                rc=$?
                if [ "$rc" -ne 0 ]; then
                        echo "ERROR:git clone failed for "$component""
                exit 1
                fi

                if [ "$component" == cortx-hare ] || [ "$component" == cortx-sspl ] || [ "$component" == cortx-ha ] || [ "$component" == cortx-py-utils ] || [ "$component" == cortx-prereq ]; then
                COMMIT_HASH="$(grep -w '*.rpm\|$component\|uniq' RELEASE.INFO | awk '!/debuginfo*/' | awk -F['_'] '{print $2}' | cut -d. -f1 |  sed 's/git//g' | grep -v ^[[:space:]]*$)";
                elif [ "$component" == "cortx-csm_agent" ] || [ "$component" == "cortx-csm_web" ]; then
                COMMIT_HASH="$(grep -w '*.rpm\|$component\|uniq' RELEASE.INFO | awk '!/debuginfo*/' | awk -F['_'] '{print $3}' | cut -d. -f1 |  sed 's/git//g' | grep -v ^[[:space:]]*$)";
                else
                COMMIT_HASH="$(grep -w '*.rpm\|$component\|uniq' RELEASE.INFO | awk '!/debuginfo*/' | awk -F['_'] '{print $2}' | cut -d. -f1 |  sed 's/git//g' | grep -v ^[[:space:]]*$)";
                fi

                echo "Component: "$component" , Repo:  "${COMPONENT_LIST[$component]}", Commit Hash: "${COMMIT_HASH}""
                pushd "$dir"
                if [ "$GIT_TAG" != "" ]; then
                        git tag -a $GIT_TAG ${COMMIT_HASH} -m $TAG_MESSAGE;
                        git push origin $GIT_TAG;
                        echo "Component: $component , Tag: git tag -l $GIT_TAG is Tagged Successfully";
                        git tag -l $GIT_TAG;
                else
                        echo "Tag is not successful. Please pass value to GIT_TAG";
                fi
                 if [ "$DEBUG" = true ]; then
                        git push origin --delete $GIT_TAG;
                 else
                        echo "Run in Debug mode if Git tag needs to be deleted";

                fi

                popd
        done
                git config --global user.email "cortx-application@seagate.com"
                git config --global user.name "cortx-admin"

                if [ "$REL_NAME" != "" ]; then
                        echo "Release will be set for all the components";

                for component in "${!REPO_LIST[@]}"

                do
                        if [ "$component" == cortx-hare ] || [ "$component" == cortx-sspl ] || [ "$component" == cortx-ha ] || [ "$component" == cortx-py-utils ] || [ "$component" == cortx-prereq ] || [ "$component" == "cortx-csm_agent" ] || [ "$component" == "cortx-csm_web" ]; then

                        echo "Component: "$component" , Repo:  "${REPO_LIST[$component]}"";

                        curl -H "Accept: application/vnd.github.v3+json"  "${REPO_LIST[$component]}" -d '{"tag_name":""$GIT_TAG"", "name":""$REL_NAME""}';              
                        else
                        echo "Release is not created.";
                        fi

                if [ "$DEBUG" = true ]; then
                        curl -X DELETE -H "Accept: application/vnd.github.v3+json"  "${REPO_LIST[$component]}"/""$REL_ID"";
                else
                        echo "Run in Debug mode if Release needs to be deleted";
                fi
                done
                else
                        echo "Please pass the value of Release";
                fi

