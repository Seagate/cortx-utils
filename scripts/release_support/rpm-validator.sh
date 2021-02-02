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

# Constants

BRANCH=$1
OS_VERSION=$2

function usage() {
    echo "No inputs provided exiting..."
    echo "Please provide Branch and OS detail.Script should be executed as.."
    echo "$0 BRANCH OS_VERSION"
    exit 1
}

if [ $# -eq 0 ]; then
usage
fi

if [ -z "$BRANCH" ]; then echo "No BRANCH provided.."; exit 1 ; fi
if [ -z "$OS_VERSION" ]; then echo "No OS_VERSION provided.."; exit 1; fi


RPM_LOCATION="http://cortx-storage.colo.seagate.com/releases/cortx/github/$BRANCH/$OS_VERSION"

# Validation Params
RPM_VERSION_EXPECTED="2.0.0"
RPM_LICENSE_EXPECTED="Seagate"

RPM_NAMING_PATTERN="cortx-[component_name]-[version]-[bld]_[git_tag].[platform].rpm"

COMPONENT_RPM_PATTERN_ARRAY=( 
                    "Motr:cortx-motr"
                    "S3:cortx-s3server,cortx-s3iamcli"
                    "Hare:cortx-hare"
                    "HA:cortx-ha"
                    "CSM:cortx-csm_agent,csm_web"
                    "Provisioner:cortx-prvsnr"
                    "SSPL:cortx-sspl"
                    "NFS:cortx-fs,cortx-dsal,cortx-nsal,cortx-utils"
                    "CORTX-utils:cortx-py-utils,stats_utils"
                )

RPM_INSTALL_ROOT_PATH="/opt/seagate/cortx"
RPM_LOG_ROOT_PATH="/var/log/cortx"
RPM_INSTALL_PATH_EXPECTED=(
                    "cortx-utils:lib" "cortx-nsal:lib" "cortx-dsal:lib" "cortx-fs:lib,conf" # NFS
                    "cortx-motr:bin,lib,conf,log"                                           # Motr
                    "cortx-s3server:bin,lib,conf,log" "cortx-s3iamcli:bin,lib,conf,log"     # S3Server
                    "cortx-hare:bin,lib,conf,log"                                           # Hare
                    "cortx-ha:bin,lib,conf,log"                                             # HA
                    "cortx-csm_agent:bin,lib,conf,log" "cortx-csm_web:bin,lib,conf,log"     # CSM
                    "cortx-prvsnr:bin,lib,conf,log"                                         # Prvsnr
                    "cortx-sspl:bin,lib,conf,log"                                           # SSPL
                    "cortx-py-utils:bin,lib,conf,log" "stats_utils:bin,lib,conf,log"        # CORTX Utils
                )

VALIDATION_ENVIRONMENT="OS : $(cat /etc/redhat-release | sed -e 's/ $//g') , Kernel : $(uname -r)"

REPORT_HTML="<!DOCTYPE html><html><body> <h1 align='center'> <b>RPM Validation </b></h1> <h3>Validation Criteria:</h3>
<b>Ref :</b> <a
href='https://seagatetechnology.sharepoint.com/:p:/r/sites/gteamdrv1/tdrive1224/Shared%20Documents/Architecture/EOS%20Specifications%20-%20EESV1.pptx?d=w8e177e3db776484a8e8f6263fcdc7830&csf=1&web=1&e=4z8Rnn&nav=eyJzSWQiOjI2NSwiY0lkIjowfQ'><i> Cortx Specifications for LDR-1</i> </a> <table id='t01' style='border: 1px solid black;border-collapse: collapse;width:
100%;background-color: #f2f2d1;'> <tr> <td style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align: left;'>RPM
Location</td><td style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align:
left;'><a href='BUILD_URL'>BUILD_URL</a></td></tr><tr> <td style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align: left;'>RPM Naming
Conventions</td><td style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align:
left;'>$RPM_NAMING_PATTERN</td></tr><tr> <td style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align: left;'>RPM Installation Path
Naming Conventions</td><td style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align:
left;'>$RPM_INSTALL_ROOT_PATH/[comp]/bin/ <br>$RPM_INSTALL_ROOT_PATH/[comp]/conf/ <br>$RPM_INSTALL_ROOT_PATH/[comp]/lib/ <br>$RPM_LOG_ROOT_PATH/[comp]/..
<br></td></tr><tr> <td style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align: left;'>RPM License</td><td
style='border: 1px solid black;border-collapse: collapse;padding: 5px;text-align: left;'>$RPM_LICENSE_EXPECTED</td></tr></table><br/><h3>Validation Environment : </h3><pre>       $VALIDATION_ENVIRONMENT</pre></p><br/>
<h3>Validation Result:</h3><table class='blueTable' style='font-family: Verdana, Geneva, sans-serif;border: 1px
solid #1C6EA4;background-color: #EEEEEE;width: 100%;text-align: left;border-collapse: collapse;table-layout: fixed ;'>
<thead style='background: linear-gradient(to bottom, #5592bb 0%, #327cad 66%, #1C6EA4 100%);border-bottom: 2px solid
#444444;'> <tr> <th>Component</th> <th>Name</th> <th>Naming Check</th> <th>License Check</th> <th>Instalation
Directory Check</th><th>Dependency Check</th></tr></thead> <tbody>VALIDATION_RESULT</tbody> </table></body></html>"

HTML_TD_STYLE="style='border: 1px solid #AAAAAA;padding: 3px 2px;font-size: 13px;'"


# Validation Logic
build_number=$(wget "${RPM_LOCATION}/last_successful/RELEASE.INFO" -q -O - | grep BUILD |  sed 's/"//g' | cut -d: -f2 | xargs )
release_rpms_array=$(wget "${RPM_LOCATION}/${build_number}/dev" -q -O - | grep -Po '(?<=href=")[^"]*' | grep -v debuginfo | grep ".rpm")

echo "RPM Validation Initiated for Build = $build_number"
BUILD_URL="${RPM_LOCATION}/${build_number}/dev"

components_rpm_array=()

_categarize_component_rpms(){

    COMPONENT_RPM_PATTERN_ARRAY=("${!1}")

    for component in ${COMPONENT_RPM_PATTERN_ARRAY[@]}
    do
        unset component_rpm_patteren_array
        unset component_name
        if [[ $component == *":"* ]]
        then
            tmp_component_rpm_group=(${component//:/ })
            component_name=${tmp_component_rpm_group[0]}
            component_rpm_patteren_array=${tmp_component_rpm_group[1]}
            component_rpm_patteren_array=(${component_rpm_patteren_array//,/ })

            rpm_list=""
            for rpm_patteren in ${component_rpm_patteren_array[@]}
            do
                for rpm in ${release_rpms_array[@]}
                do
                    if [[ "$rpm" == *"$rpm_patteren-"* ]]; then
                        rpm_list="$rpm,$rpm_list"
                    fi
                done
            done
            components_rpm_array+=("$component_name:$rpm_list")
        fi
    done  
}

_validate_rpm_install_path(){

    rpm_install_path_data="$1"
    rpm_name="$2"
    component_name=$(echo "$3" | tr '[:upper:]' '[:lower:]')
    result=""
    rpm_name_main_input=$(echo "$rpm_name" | cut -d- -f1,2)
    rpm_module_name_input=$(echo "$rpm_name" | cut -d- -f2)
    if [[ ( "$rpm_module_name_input" == *"$component_name"* ) || ( "$rpm_name" != "prvsnr" ) ]]; then
        rpm_module_name_input=$component_name 
    fi

    for rpm_install_path in ${RPM_INSTALL_PATH_EXPECTED[@]}
    do
        if [[ $rpm_install_path == *":"* ]]
        then
            tmp_rpm_install_path=(${rpm_install_path//:/ })
            rpm_moudle_name=${tmp_rpm_install_path[0]}
            if [[ "$rpm_moudle_name" == "$rpm_name_main_input" ]]; then
            
                rpm_install_path_array=${tmp_rpm_install_path[1]}
                rpm_install_path_array=(${rpm_install_path_array//,/ })

                for folder_name in ${rpm_install_path_array[@]}
                do
                    PATH="$RPM_INSTALL_ROOT_PATH/$rpm_module_name_input/$folder_name"
                    if [[ "$folder_name" == "log" ]]; then
                        PATH="$RPM_LOG_ROOT_PATH/$rpm_module_name_input" 
                    fi
                    
                    if [[ "$rpm_install_path_data" != *"$PATH"* ]]; then
                        result="$folder_name, $result"
                        echo "[$rpm_name] : $PATH : Absent" >> rpm_path_validate.log
					else
						echo "[$rpm_name] : $PATH : Present" >> rpm_path_validate.log
                    fi
                done
                break
            fi
        fi
    done
    echo "$result"
}

_prepare(){

    rpm --import "$BUILD_URL/RPM-GPG-KEY-Seagate"
    yum-config-manager --add-repo "$BUILD_URL"

cat > /etc/yum.repos.d/cortx-build.repo <<- EOF
[cortx-build-repo]
name=Cortx Release Build Repo
baseurl=$BUILD_URL
enabled=1
gpgcheck=1
gpgkey=$BUILD_URL/RPM-GPG-KEY-Seagate
priority=1
EOF

cat > /etc/yum.repos.d/salt.repo <<- EOF
[saltstack-repo]
name=SaltStack repo for RHEL/CentOS $releasever
baseurl=https://archive.repo.saltstack.com/py3/redhat/7.0/x86_64/archive/2019.2.1/
enabled=1
gpgcheck=1
gpgkey=https://archive.repo.saltstack.com/py3/redhat/7.0/x86_64/archive/2019.2.1/SALTSTACK-GPG-KEY.pub
priority=1
EOF

}

_clean(){
    rm -rf /etc/yum.repos.d/salt.repo
    rm -rf /etc/yum.repos.d/cortx-build.repo
    rm -rf /etc/yum.repos.d/luster.repo
}

_generate_rpm_validation_report(){

    local validation_rpms=("${!1}")
    validation_result_html=""

    for component_rpm_group in ${validation_rpms[@]}
    do
        unset component_name
        unset component_rpms
        rpm_check_result_html=""
        tmp_rpm_array=(${component_rpm_group//:/ })
        component_name=${tmp_rpm_array[0]}
        component_rpms=${tmp_rpm_array[1]}
        component_rpms=(${component_rpms//,/ })

        for rpm in ${component_rpms[@]}
        do
            echo "[$component_name] : validating $rpm"
            rpm_name=$(rpm -qp "$BUILD_URL/$rpm" --qf '%{NAME}')
            rpm_license=$(rpm -qp "$BUILD_URL/$rpm" --qf '%{LICENSE}')
            rpm_release=$(rpm -qp "$BUILD_URL/$rpm" --qf '%{RELEASE}')
            rpm_arch=$(rpm -qp "$BUILD_URL/$rpm" --qf '%{ARCH}')
            rpm_files=$(rpm -qp "$BUILD_URL/$rpm" --qf '[%{FILENAMES}]')

            RPM_NAMING_PATTERN="cortx-[component_name]-[version]-[bld]_[git_tag].[platform].rpm"

            rpm_name_expected=$(echo -e "$RPM_NAMING_PATTERN" | sed -e "s/cortx-\[component_name\]/$rpm_name/g;s/\[version\]/$RPM_VERSION_EXPECTED/g; s/\[bld\]_\[git_tag\]/$rpm_release/g; s/\[platform\]/$rpm_arch/g")

            name_check="<td $HTML_TD_STYLE><span style='color:green; text-shadow: -2px 0 black, 0 2px black, 2px 0 black, 0 -2px black; font-size: 30px;'>&#10003;</span></td>"
            if [[ "$rpm" != "$rpm_name_expected" ]]
            then
                name_check="<td $HTML_TD_STYLE><b>Invalid RPM Name :</b> <br> - <b><i>Expected : </b></i>$rpm_name_expected<br> -  <b><i>Actual : </b></i>$rpm</td>"
            fi

            license_check="<td $HTML_TD_STYLE><span style='color:green; text-shadow: -2px 0 black, 0 2px black, 2px 0 black, 0 -2px black; font-size: 30px;'>&#10003;</span></td>"
            if [[ "$rpm_license" != "$RPM_LICENSE_EXPECTED" ]]
            then
                license_check="<td $HTML_TD_STYLE><b>Invalid License :</b> <br> - <b><i>Expected :</b></i> $RPM_LICENSE_EXPECTED<br> - <b><i>Actual :</b></i>$rpm_license</td>"
            fi

            if [ "$rpm_name" == "cortx-sspl-test" ] || [ "$rpm_name" == "cortx-sspl-cli" ]; then
                install_path_check="<td $HTML_TD_STYLE><B>Path Check excluded : </b></td>"
             else   
                install_path_check=$(_validate_rpm_install_path "$rpm_files" "$rpm_name" "$component_name")
                if [[ ! -z "$install_path_check" ]]
                then
                    install_path_check="<td $HTML_TD_STYLE><B>Path Does Not Exists : </b>${install_path_check%??}</td>"
                else
                    install_path_check="<td $HTML_TD_STYLE><span style='color:green; text-shadow: -2px 0 black, 0 2px black, 2px 0 black, 0 -2px black; font-size: 30px;'>&#10003;</span></td>"
                fi
            fi

            dependency_check=$({ yum install "$BUILD_URL/$rpm" --assumeno; } 2>&1 >/dev/null)
            if [ ! -z "$dependency_check" ]; then
                dependency_check="<td><details><summary>Error Log</summary><p>$dependency_check</p></details></td>"
            else
                dependency_check="<td $HTML_TD_STYLE><span style='color:green; text-shadow: -2px 0 black, 0 2px black, 2px 0 black, 0 -2px black; font-size: 30px;'>&#10003;</span></td>"
            fi
            rpm_check_result_html+="<tr><td $HTML_TD_STYLE><b>$rpm_name</td>$name_check $license_check $install_path_check $dependency_check</tr>"        
       
        done

        validation_result_html+="<tr><td rowspan=$((${#component_rpms[@]}+1)) style='border: 1px solid #AAAAAA;padding: 3px 2px;font-size: 13px;'><b>$component_name</b></td></tr>$rpm_check_result_html"

    done

    REPORT_HTML=$(echo -e "$REPORT_HTML" | sed -e "s=BUILD_URL=$BUILD_URL=g;" )

    echo "${REPORT_HTML/VALIDATION_RESULT/$validation_result_html}" > rpm_validation.html
}

_prepare

_categarize_component_rpms COMPONENT_RPM_PATTERN_ARRAY[@]

_generate_rpm_validation_report components_rpm_array[@]

_clean
