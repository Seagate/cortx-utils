#!/bin/bash - 
##======================================================================
# This script is meant for quick & easy install via:
#   $ sh install.sh
#========================================================================      
#	title           	: install.sh
#	description     	: This script will install single node cluster on provided machine.
#	author		 		: RE
#	date            	: 20200210
#	version         	: 0.1   
#	usage		 		: bash install.sh -build {BUILD_ID}
#    						-b  = Build ID
#	bash_version    	: 4.2.46(2)-release
#=========================================================================

# Set Build Log Path /tmp/seaget/log
LOG_PATH="/tmp/seaget/log"
LOGFILE="${LOG_PATH}/setup_provnr.log"
RESULTLOG="${LOG_PATH}/result.log"
RELEASE_NOTES="${LOG_PATH}/RELEASE_NOTES.log"

mkdir -p ${LOG_PATH}
touch ${RELEASE_NOTES}

setup_provnr(){
    
    BUILD=$1

    if [[ $BUILD == ees* ]] || [[ $BUILD == eos* ]] || [[ $BUILD == nightly* ]]
    then
        TARGET_BUILD="${BUILD}"
    else
        TARGET_BUILD="integration/centos-7.7.1908/${BUILD}"
    fi

    DEFAULT_REPO="http://cortx-storage.colo.seagate.com/releases/eos" 
    REPO="${DEFAULT_REPO}/${TARGET_BUILD}"
    RELEASE_NOTES_URL="${REPO}/RELEASE_NOTES.txt"
    HOST=`hostname`

    echo "================================================================================"
    echo "  Target Build  : ${TARGET_BUILD}"
    echo "  Repository    : ${REPO}"
    echo "  Host Name     : ${HOST}" 
    echo "================================================================================"

    # Install Provisioner 
    yum install -y yum-utils wget;
    yum-config-manager --add-repo ${REPO}
    yum install eos-prvsnr-cli -y --nogpgcheck;

     wget -O $RELEASE_NOTES $RELEASE_NOTES_URL

cat <<-EOF >>/root/.ssh/config
Host eosnode-1
    HostName ${HOST}
    User root
    UserKnownHostsFile /dev/null
    StrictHostKeyChecking no
    IdentityFile /root/.ssh/id_rsa_prvsnr
    IdentitiesOnly yes
EOF

    chown root /root/.ssh/config
    chmod 644 /root/.ssh/config

    cd /opt/seagate/eos-prvsnr/cli;
    sh /opt/seagate/eos-prvsnr/cli/setup-provisioner -S
    
    provnr_status=$(salt eosnode-1 test.ping)
    if [[ "$provnr_status" == *"True"* ]]; then
        echo "[ SETUP_PROVISIONER_STATUS : SUCCESS ]"
    fi

    sed -i "s/mgmt0/eth0/g;s/data0/eth1/g;s/hostname: eosnode-1/hostname: ${HOST}/g" /opt/seagate/eos-prvsnr/pillar/components/cluster.sls;
    sed -i "s:integration/centos-7.7.1908/last_successful/:${TARGET_BUILD}:g" /opt/seagate/eos-prvsnr/pillar/components/release.sls;

    # Limit number instance for run (VM Constrain)
    sed -i "s/nbproc: [0-9]\+/nbproc: 2/g" /opt/seagate/eos-prvsnr/pillar/components/haproxy.sls;	
	sed -i "s/no_of_inst: [0-9]\+/no_of_inst: 2/g" /opt/seagate/eos-prvsnr/pillar/components/s3server.sls;

    salt "*" saltutil.refresh_pillar
}

scan_ssa_hba(){
    yum install sg3_utils -y;
    rescan-scsi-bus.sh;
}

host_check(){   
    lsblk
    ip -a
}

deploy_eos(){
    sh /opt/seagate/eos-prvsnr/cli/deploy-eos -S
}

bootstrap_eos(){
    sh /opt/seagate/eos-prvsnr/cli/bootstrap-eos -S
}


validate(){
    STEP=$1
    echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
    if grep -iEq "Result: False|ERROR:|\[ERROR   \]" "${LOGFILE}"
    then
        echo " *** [ $STEP ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
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
    elif [[ "$(validate_stack "$1")"  == "1" ]];
    then
        echo " *** [ $STEP ] EXECUTION STATUS : FAILED" 2>&1 | tee -a "${RESULTLOG}"
        echo "==========================================================" 2>&1 | tee -a "${RESULTLOG}"
        echo "FAILURE CAUSE:" 2>&1 | tee -a "${RESULTLOG}"
        echo "  ERROR : $STEP - Basic Checks are failed" 2>&1 | tee -a "${RESULTLOG}"
        echo "=============================================================<END" 2>&1 | tee -a "${RESULTLOG}"
        exit 0
    else
        echo " *** [ $STEP ] EXECUTION STATUS : SUCCESS" 2>&1 | tee -a "${RESULTLOG}"
    fi
}

validate_stack(){

    STACK_NAME=$1
    STATUS=1
    case $STACK_NAME in
        SETUP_PROVISONER) if grep -iEq "\[ SETUP_PROVISIONER_STATUS : SUCCESS \]" "${LOGFILE}"; then STATUS=0 ; fi ;;
        SCAN_SAS_HBA)     if grep -iEq "Scanning SCSI subsystem for new devices" "${LOGFILE}"; then STATUS=0 ; fi ;;
        DEPLOY_EOS)       if grep -iEq "Result: True" "${LOGFILE}"; then STATUS=0 ; fi ;;
        BOOTSTRAP_EOS)    if grep -iEq "Result: True" "${LOGFILE}"; then STATUS=0 ; fi ;;
    esac
    echo $STATUS
}


cleanup() {
    sed  -i 's/\x1b\[[0-9;]*m//g' "${LOGFILE}"
    sed  -i 's/\x1b\[[0-9;]*m//g' "${RESULTLOG}"
}

trap cleanup  0 1

while getopts ":b:" opt; do
  case $opt in
    b) BUILD="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

# Validate Input
if [ -z "$BUILD" ]
  then
    echo "Invalid execution... Please provide valid argument"
    exit 1
fi


# 1.Setup Provisioner
echo "================================================================================"
echo "1. Setup Provisioner"
echo "================================================================================"
setup_provnr $BUILD 2>&1 | tee -a "${LOGFILE}"
validate 'SETUP_PROVISONER'

# 2.Scan SAS HBA
echo "================================================================================"
echo "2.Scan SAS HBA"
echo "================================================================================"
scan_ssa_hba 2>&1 | tee -a "${LOGFILE}"
validate 'SCAN_SAS_HBA'

# 3.Deploy EOS
echo "================================================================================"
echo "3.Deploy EOS"
echo "================================================================================"
deploy_eos 2>&1 | tee -a "${LOGFILE}"
validate 'DEPLOY_EOS'

# 4.Bootstrap EOS
echo "================================================================================"
echo "4. Bootstrap EOS"
echo "================================================================================"
bootstrap_eos  2>&1 | tee -a "${LOGFILE}"
validate 'BOOTSTRAP_EOS'

touch "${LOG_PATH}/success"