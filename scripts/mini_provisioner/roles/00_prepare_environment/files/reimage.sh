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

# Mthod will perform REST operations 'GET', 'POST'

_do_rest(){

    REST_ENDPOINT="$1"
    REST_CRED="$2"
    REST_METHOD="$3"
    REST_DATA="$4"

    response=$(curl -s --insecure --user "${REST_CRED}" -H "Accept: application/json" --request "${REST_METHOD}" ${REST_DATA} "${REST_ENDPOINT}" )     
    echo "${response}"
}


# Verify/install the required dependency before execution
_check_dependencies(){

    _console_log " [ _check_dependencies ] : Initiated......"

    declare -a dependency_tools=("jq" "nmap")

    for dt in "${dependency_tools[@]}"
    do
       if command -v "${dt}" >/dev/null 2>&1 ; then
            _console_log " [ _check_dependencies ] : '${dt^^}' Already Installed "
        else
            _console_log " [ _check_dependencies ] : '${dt^^}' Not Found, Started installing '${dt^^}'....."

            if [ -f /etc/redhat-release ]; then
                yum install "${dt}" -y
            elif [ -f /etc/lsb-release ]; then
                apt-get install "${dt}" -y
            fi
        fi

    _console_log " [ _check_dependencies ] : '${dt^^}' Version Installed : $(${dt} --version | sed -r '/^\s*$/d' | head -n 1)"
    done
}

# Generic logging mechanisum
_console_log(){

    MESSAGE="$1"
    TYPE="$2"

    underline="----------------------------------------------------------------------------"
    
    if [ "${TYPE}" == "0" ]; then
        printf "\n\n"
        echo "$(date) : ${MESSAGE}" >&2
        echo ${underline:0:${#MESSAGE}} >&2
        printf "\n\n"
    elif [ "${TYPE}" == "1" ]; then
        echo -ne "${MESSAGE}" >&2
    else
        echo "$(date) : ${MESSAGE}" >&2
    fi
}

#Generic Json Response quering using JQ
_get_response(){
    DATA="$1"
    KEY="$2"
    if [ -z "${DATA}" ] || [ -z "${KEY}" ];
    then
        _console_log "[ _get_response ] : API Response is Null  - '${ACTION}'" 1
        exit 1
    else
        result=$(echo "${DATA}" | jq -r ".${KEY}" | tr -d '[ \n]')
        echo "${result}"
    fi
}

# Cloudform REST Request catelog
_cloudform(){

    ACTION="$1"

    #_console_log "[ _cloudform ] : Action Initiated - '$ACTION'"
    
    case $ACTION in
        GET_VM)
            QUERY_DATA="-G --data-urlencode expand=resources --data-urlencode attributes=name,vendor,snapshots --data-urlencode filter[]=name=${VM_NAME}"
            response=$(_do_rest "${CF_VM_SEARCH_ENDPOINT}" "${CF_CRED}" "GET" "${QUERY_DATA}")
        ;;
        GET_VM_STATUS)
            response=$(_do_rest "${CF_VM_ENDPOINT}" "${CF_CRED}" "GET" "")
            response=$(_get_response "${response}" 'power_state')
        ;;
        START_VM) 
            _refresh_vm
            POST_DATA="--data {\"action\":\"start\"}"
            response=$(_do_rest "${CF_VM_ENDPOINT}" "${CF_CRED}" "POST" "$POST_DATA")
            response=$(_get_response "${response}" 'message')
        ;;
        STOP_VM)
            _refresh_vm
            POST_DATA="--data {\"action\":\"stop\"}"
            response=$(_do_rest "${CF_VM_ENDPOINT}" "${CF_CRED}" "POST" "$POST_DATA")
            response=$(_get_response "${response}" 'message')
        ;;
        REVERT_VM_SNAPSHOT)
            _refresh_vm
            POST_DATA="--data {\"action\":\"revert\"}"
            response=$(_do_rest "${CF_VM_SNAPSHOT_ENDPOINT}" "${CF_CRED}" "POST" "$POST_DATA")
            response=$(_get_response "${response}" 'task_href')
        ;;
        REFRESH_VM)
            POST_DATA="--data {\"action\":\"refresh\"}"
            response=$(_do_rest "${CF_VM_ENDPOINT}" "${CF_CRED}" "POST" "$POST_DATA")
            response=$(_get_response "${response}" 'message')
        ;;
        GET_API)
            response=$(_do_rest "${CF_API_ENDPOINT}" "${CF_CRED}" "GET" "")
        ;;
        GET_TASK_STATUS)
            response=$(_do_rest "${CF_TASK_ENDPOINT}" "${CF_CRED}" "GET" "")
        ;;    
    esac 

    echo "${response}"
}

# Preload functinalities
_preload() {

    _console_log " [1] - Pre Checks Initiated for VM : ${VM_NAME}" 0

    CF_HOST="https://ssc-cloud.colo.seagate.com"
    CF_API_ENDPOINT="${CF_HOST}/api"
    CF_VM_SEARCH_ENDPOINT="${CF_HOST}/api/vms"

    
    _check_dependencies

    _validate_input_params

    response=$(_cloudform 'GET_VM')
    CF_VM_ENDPOINT=$(echo "${response}" | jq -r '.resources[0].href')
    CF_VM_SNAPSHOT_ENDPOINT="${CF_VM_ENDPOINT}/snapshots/$(echo ${response} | jq -r '.resources[0].snapshots |=sort_by(.created_on) | .resources[0].snapshots[0].id')"

    _console_log " [ _preload ] : VM_HOST - ${VM_HOST}"
    _console_log " [ _preload ] : CF_VM_ENDPOINT - ${CF_VM_ENDPOINT}"
    _console_log " [ _preload ] : CF_VM_SNAPSHOT_ENDPOINT - ${CF_VM_SNAPSHOT_ENDPOINT}"
}

# Logic to ensure VM state change
_wait_for_vm_state_change() {

    expected_vm_state="$1"
    current_vm_state=$(_cloudform 'GET_VM_STATUS')

    n=0
    _console_log " [ _wait_for_vm_state_change ] :" 1

    # wait for ~ 30 mins
    while [ "$n" -lt 60 ] && [ "${expected_vm_state}" != "${current_vm_state}" ]; do
        current_vm_state=$(_cloudform 'GET_VM_STATUS')
        _console_log "=>" 1
        n=$(( n + 1 ))
        sleep 30
    done
    _console_log "Done"
}

# Change VM state based on input param
_change_vm_state(){

    change_vm_state="$1"
    retry_on_fail="$2"
    current_vm_state=$(_cloudform 'GET_VM_STATUS')

    _console_log " [ _change_vm_state ] : Current VM State - '${current_vm_state}' , Expected VM State Change - '${change_vm_state}' "
    
    if [ "${current_vm_state}" != "${change_vm_state}" ];then

        if [ "${change_vm_state}" == "on" ];then
            vm_change_state_response=$(_cloudform 'START_VM')
        else
            vm_change_state_response=$(_cloudform 'STOP_VM')
        fi
        _console_log " [ _change_vm_state ] : Change Request Message - ${vm_change_state_response}"
        
        _wait_for_vm_state_change "${change_vm_state}"
        
        current_vm_state=$(_cloudform 'GET_VM_STATUS')

        if [ "${change_vm_state}" == "${current_vm_state}" ];then
            _console_log "[ _change_vm_state ] : VM State changed to ${current_vm_state} successfully"
        else

            if [ "${retry_on_fail}" == "1" ];then
               
                _console_log "[ _change_vm_state ] : Retry Initated current VM State - ${current_vm_state}"
                
                # TEMP FIX for VM Issue
                _cloudform 'STOP_VM'
                _cloudform 'START_VM'

                _change_vm_state "${change_vm_state}"
            else
                _console_log "[ _change_vm_state ] : Failed to change VM State, Something went wrong..."
                exit 1
            fi
        fi
    else
        _console_log " [ _change_vm_state ] : VM State UnChanged"
    fi
}

# Revert VM Sanpshot by calling cloudform rest api
_revert_vm_snapshot(){
    CF_TASK_ENDPOINT=$(_cloudform 'REVERT_VM_SNAPSHOT')
    expected_task_state="Finished"
    expected_task_status="Ok"
    mins=0
    while [ "$mins" -lt 30 ] && [ "${expected_task_state}" != "${current_task_state}" ] && [ "${expected_task_status}" != "${current_task_status}" ]; do
        task_response=$(_cloudform 'GET_TASK_STATUS')
        current_task_state=$(_get_response "${task_response}" 'state')
        current_task_status=$(_get_response "${task_response}" 'status')
        mins=$(( mins + 1 ))
        sleep 60
    done
    task_response=$(_cloudform 'GET_TASK_STATUS')
    revert_snapshot_task_response=$(_get_response "${task_response}" 'message')
    _console_log " [ _revert_vm_snapshot ] : Revert Request Message - ${revert_snapshot_task_response}"
}

# Validate VM access by ping and ssh connection check
_validate_vm_access(){

    n=0
    host_ping_status="down"
    ssh_connection_status="not_ok"
    _console_log " [ _validate_vm_access ] Checking 'Host Ping' & 'SSH Connection' Status for the Host : $VM_HOST"

    while [[  ("$n" -lt 60 ) && ("${host_ping_status}" != "up" || "${ssh_connection_status}" != "ok") ]] ; do
    
        ping -c 1 -W 1 "${VM_HOST}" >> /dev/null 2>&1 
        ping_status=$?
        [ ${ping_status} -eq 0 ] && host_ping_status="up" || host_ping_status="down"

        nmap_status=$(nmap "${VM_HOST}" -PN -p ssh | egrep '22/tcp open  ssh')

        [ -z "${nmap_status}" ] && ssh_connection_status="not_ok" || ssh_connection_status="ok"
    
        _console_log "=>" 1
        n=$(( n + 1 ))
        sleep 30
    done
    _console_log ""
    _console_log " [ _validate_vm_access ] Host Ping Status : ${host_ping_status}"
    _console_log " [ _validate_vm_access ] SSH Connection Status : ${ssh_connection_status}"

    if [ "${host_ping_status}" != "up" ] || [ "${ssh_connection_status}" != "ok" ]
    then
        echo "** [_validate_vm_access] :  Host Unreachable, Something went wrong..."
        exit 1
    fi
}

# Refresh VM to solve power state issue
_refresh_vm(){
    refresh_vm_response=$(_cloudform 'REFRESH_VM')
    _console_log " [ _refresh_vm ] : Refresh VM Request Message - ${refresh_vm_response}"
    sleep 30
}

# Print failure message of exit 1
failure_trap() {
    _console_log " [ FAILED ] : Unable to Provision Cloudform VM"
    _refresh_vm
}

# Validate input paramater
_validate_input_params(){


    _console_log " [ _validate_input_params ] : Initiated......"


    if [ -z "${VM_NAME}" ] || [ -z "${CF_CRED}" ]
    then
        _console_log "[ _validate_input_params ] : ** Please provide valid arguments -h <HOST> & -x <CF_CRED>"
        exit 1
    fi

    cloudform_api_response=$(_cloudform 'GET_API')
    if [[ "${cloudform_api_response}" == *"unauthorized"* ]]; then
        _console_log " [ _validate_input_params ] : ERROR - Invalid Cloudform Auth Token, Please check the credentials and retry it again"
        exit 1
    fi

    cloudform_vm_search_result=$(_cloudform 'GET_VM')
    has_vm_object=$(echo "${cloudform_vm_search_result}" | jq '.resources | length')
    if [[ "${has_vm_object}" != "1" ]]; then
        _console_log " [ _validate_input_params ] : ERROR - Unable to find VM, Please verify the given VM Host is belongs to provided cloudform token account"
        exit 1
    fi
}

trap failure_trap 1


while getopts ":h:x:" opt; do
  case $opt in
    h) VM_HOST="$OPTARG"
    ;;
    x) CF_CRED="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

_console_log "Infra Setup Initiated........." 0
_console_log "================================================================================"
_console_log "  VM Host    : ${VM_HOST}"
_console_log "  Datetime   : $(date)"
_console_log "================================================================================"

VM_NAME=$(echo ${VM_HOST%%.*})    
_preload 

if [ -z "${CF_VM_ENDPOINT}" ] || [ -z "${CF_VM_SNAPSHOT_ENDPOINT}" ]
  then
    echo "** Something went wrong, _preload params are not valid"
    exit 1
fi

_refresh_vm

_console_log "[2] - Stop VM Initiated : ${VM_NAME}" 0
_change_vm_state "off" "1"

_console_log "[3] - VM Snapshot Reverte Initiated : ${VM_NAME}" 0
_revert_vm_snapshot

_console_log "[4] - Start VM Initiated : ${VM_NAME}" 0
_change_vm_state "on" "1"

_console_log "[5] - Validating VM access : ${VM_NAME}" 0
_validate_vm_access

_console_log " [ SUCCESS ] : VM Provisoned Successfully" 0

exit 0