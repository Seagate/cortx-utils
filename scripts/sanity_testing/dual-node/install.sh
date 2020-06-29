#!/bin/bash - 
##======================================================================
# This script is meant for quick & easy install via:
#   $ sh install.sh
#========================================================================      
#	title           	: install.sh
#	description     	: This script will install dual node cluster on provided machine.
#	author		 		: RE
#	date            	: 20200210
#	version         	: 0.1   
#	usage		 		: bash install.sh -b {BUILD_ID} -s {NODE_1} -c {NODE_2} -p {SSH_PASS}
#    						-b  = Build ID
#                           -s  = Server (NODE 1) HOST
#                           -c  = Client (NODE 2) HOST
#                           -p  = SSH PASS
#	bash_version    	: 4.2.46(2)-release
#   ref                 : http://gitlab.mero.colo.seagate.com/eos/provisioner/ees-prvsnr/wikis/Setup-Guides/QuickStart-Guide
#=========================================================================

_pre_process(){

    LOG_PATH="/tmp/seaget/log"
    LOGFILE="${LOG_PATH}/setup_provnr.log"
    RESULTLOG="${LOG_PATH}/result.log"
    MANIFEST_FILE="${LOG_PATH}/MANIFEST.log"

    mkdir -p ${LOG_PATH}
    touch ${MANIFEST_FILE}

    yum install -y yum-utils wget expect sshpass;
    wget -O "${MANIFEST_FILE}" "${REPO}/MANIFEST.MF"
}

_setup_provnr(){
    
    BUILD=$1
    NODE1_HOST=$2
    NODE2_HOST=$3

    # 1. Validation
    if [[ $BUILD == ees* ]] || [[ $BUILD == eos* ]] || [[ $BUILD == nightly* ]]
    then
        TARGET_BUILD="${BUILD}"
    else
        TARGET_BUILD="integration/centos-7.7.1908/${BUILD}"
    fi

    # 2. Install Reference
    DEFAULT_REPO="http://ci-storage.mero.colo.seagate.com/releases/eos" 
    REPO="${DEFAULT_REPO}/${TARGET_BUILD}"

    echo "================================================================================"
    echo "  Target Build  : ${TARGET_BUILD}"
    echo "  Repository    : ${REPO}"
    echo "  Node 1 Host   : ${NODE1_HOST}" 
    echo "  Node 2 Host   : ${NODE2_HOST}" 
    echo "================================================================================"

    # 3. Install Provisioner 
   
    yum-config-manager --add-repo ${REPO}
    yum install eos-prvsnr-cli -y --nogpgcheck;
   
    sshpass -p ${SSH_PASS} ssh -o StrictHostKeyChecking=no ${NODE2_HOST} """      
      yum install -y yum-utils sshpass;
      yum-config-manager --add-repo ${REPO}
      yum install eos-prvsnr-cli -y --nogpgcheck;
    """
    
    # 4. Provisioner Install & Setup
    sh /opt/seagate/eos-prvsnr/cli/setup-provisioner --eosnode-2=${NODE2_HOST} ${REPO}

     # 6. Config Updates
    NODE1_IP=$(ping -c1 ${NODE1_HOST} | sed -nE 's/^PING[^(]+\(([^)]+)\).*/\1/p')
    NODE2_IP=$(ping -c1 ${NODE2_HOST} | sed -nE 's/^PING[^(]+\(([^)]+)\).*/\1/p')

    CLUSTER_SLS_FILE="/opt/seagate/eos-prvsnr/pillar/components/cluster.sls"
    rm -f ${CLUSTER_SLS_FILE}
    wget -O ${CLUSTER_SLS_FILE} http://gitlab.mero.colo.seagate.com/re-poc/node-setup/raw/master/dual-node/config/cluster.sls

    sed -i "s:<NODE1_HOST>:${NODE1_HOST}:g;s:<EOS_NODE1_IP>:${NODE1_IP}:g;s:<NODE2_HOST>:${NODE2_HOST}:g;s:<EOS_NODE2_IP>:${NODE2_IP}:g" ${CLUSTER_SLS_FILE}; 
   

    # Limit number instance for run (VM Constrain)
    sed -i "s/nbproc: [0-9]\+/nbproc: 2/g" /opt/seagate/eos-prvsnr/pillar/components/haproxy.sls;	
	sed -i "s/no_of_inst: [0-9]\+/no_of_inst: 2/g" /opt/seagate/eos-prvsnr/pillar/components/s3server.sls;

    salt '*' saltutil.refresh_pillar; salt '*' saltutil.sync_all

    if [[ "$(salt eosnode-2 test.ping)" == *"True"* ]]; then
        echo "[ _setup_provnr ] :  NODE 1 STATUS - SUCCESS"
    fi
    if [[ "$(salt eosnode-1 test.ping)" == *"True"* ]]; then
        echo "[ _setup_provnr ] :  NODE 2 STATUS - SUCCESS"
    fi 
    echo " [ _setup_provnr ] : Setup Provisoner for Dual node is completed" 
}

_scan_ssa_hba(){
    yum install sg3_utils -y;
    rescan-scsi-bus.sh;
}

_host_check(){   
    lsblk
    ip -a
}

_deploy_eos(){
    sh /opt/seagate/eos-prvsnr/cli/deploy-eos -v;
}

_check_for_errors_in_log(){
    STACK_NAME=$1
    echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
    if grep -iEq "Result: False|\[ERROR   \]" "${LOGFILE}"
    then
        echo " *** [ $STACK_NAME ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
        echo "FAILURE CAUSE:" 2>&1 | tee -a "${RESULTLOG}"

        if grep -iEq "Result: False" "${LOGFILE}"
        then
            grep -B 4 -A 3 "Result: False" "${LOGFILE}" 2>&1 | tee -a "${RESULTLOG}"
        fi
        
        if grep -iEq "ERROR:" "${LOGFILE}"  
        then
            grep  -B 1 -A 2 "ERROR:" "${LOGFILE}"  2>&1 | tee -a "${RESULTLOG}"
        fi
        
        if grep -iEq "\[ERROR   \]" "${LOGFILE}"
        then
            grep -B 1 -A 3 "\[ERROR   \]" "${LOGFILE}" 2>&1 | tee -a "${RESULTLOG}"
        fi
        echo "==========================================================<<END" 2>&1 | tee -a "${RESULTLOG}"
        exit 0
    fi
}

_validate_stack(){

    STACK_NAME=$1
    STATUS=1
    case $STACK_NAME in
        SETUP_PROVISONER) 
            if grep -iEq "NODE 1 STATUS - SUCCESS" "${LOGFILE}" && grep -iEq "NODE 2 STATUS - SUCCESS" "${LOGFILE}"; then
                _check_for_errors_in_log $STACK_NAME
                STATUS=0 ;
            fi 
        ;;
        SCAN_SAS_HBA)     
            if grep -iEq "Scanning SCSI subsystem for new devices" "${LOGFILE}"; then 
                _check_for_errors_in_log $STACK_NAME
                STATUS=0 ; 
            fi 
        ;;
        DEPLOY_EOS)       
            if grep -iEq "Result: True" "${LOGFILE}"; then 
                _check_for_errors_in_log $STACK_NAME
                STATUS=0 ; 
            fi 
        ;;
        BOOTSTRAP_EOS)    
            if grep -iEq "Result: True" "${LOGFILE}"; then 
                _check_for_errors_in_log $STACK_NAME
                STATUS=0 ; 
            fi 
        ;;
    esac

    if [[ "$STATUS"  == "1" ]];
    then
        echo " *** [ $STACK_NAME ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
        echo "FAILURE CAUSE:" 2>&1 | tee -a "${RESULTLOG}"
        echo "ERROR : $STACK_NAME - BASIC CHECKS ARE FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "=============================================================<END" 2>&1 | tee -a "${RESULTLOG}"
        exit 0
    else
        echo " *** [ $STACK_NAME ] EXECUTION STATUS : SUCCESS" 2>&1 | tee -a "${RESULTLOG}"
    fi

    echo $STATUS
}

_cleanup() {
    sed  -i 's/\x1b\[[0-9;]*m//g' "${LOGFILE}"
    sed  -i 's/\x1b\[[0-9;]*m//g' "${RESULTLOG}"
}

trap _cleanup 0 1

while getopts ":b:s:c:p:" opt; do
  case $opt in
    b) BUILD="$OPTARG"
    ;;
    s) NODE1_HOST="$OPTARG"
    ;;
    c) NODE2_HOST="$OPTARG"
    ;;
    p) SSH_PASS="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# _validate_stack Input
if [ -z "$BUILD" ] || [ -z "$NODE1_HOST" ] || [ -z "$NODE2_HOST" ] || [ -z "$SSH_PASS" ] 
  then
    echo "Invalid execution... Please provide valid argument"
    exit 0
fi

_pre_process

# 1.Setup Provisioner
echo "================================================================================"
echo "1. Setup Provisioner"
echo "================================================================================"
_setup_provnr $BUILD $NODE1_HOST $NODE2_HOST 2>&1 | tee -a "${LOGFILE}"
_validate_stack 'SETUP_PROVISONER'

# 2.Scan SAS HBA
echo "================================================================================"
echo "2.Scan SAS HBA"
echo "================================================================================"
_scan_ssa_hba 2>&1 | tee -a "${LOGFILE}"
_validate_stack 'SCAN_SAS_HBA'

# 3.Deploy EOS
echo "================================================================================"
echo "3.Deploy EOS"
echo "================================================================================"
_deploy_eos 2>&1 | tee -a "${LOGFILE}"
_validate_stack 'DEPLOY_EOS'

touch "${LOG_PATH}/success"