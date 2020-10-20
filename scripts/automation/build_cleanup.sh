#!/bin/bash

# Input Parameter
REMOVE_BUILD_OLDER_THEN=30
KEEP_BUILD=5
ENV=""
CLEANUP_MODE="dry-run"

helpFunction()
{
   echo ""
   echo "Usage: $0 -e dev -k 5 -r 30 -m dryrun"
   echo -e "\t-a Environment where we need to execute the cleanup eg dev"
   echo -e "\t-k Number of builds to keep. eg - 5"
   echo -e "\t-r Remove builds older than x days. eg - 30"
   echo -e "\t-m Execution mode. eg 'cleanup' - deletes the builds, others- Dry Run"
   exit 1 
}

while getopts ":e:m:k:r:" opt
do
   case "$opt" in
        e ) ENV="$OPTARG" ;;
        m ) CLEANUP_MODE="$OPTARG" ;;
        k ) KEEP_BUILD="$OPTARG" ;;
        r ) REMOVE_BUILD_OLDER_THEN="$OPTARG" ;;
        ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

TOP_LEVEL_DIR=( 
    "/mnt/bigstorage/releases/cortx/github/" 
    "/mnt/bigstorage/releases/cortx/" 
    "/mnt/bigstorage/releases/cortx/github/${ENV}/rhel-7.7.1908/"
)

CLEANUP_DIR=(
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/cortx-ha"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/csm"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/csm-agent"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/csm-web"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/hare"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/mero"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/motr"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/nfs"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/provisioner"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/dev/s3server"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/prod/s3server"
    "/mnt/bigstorage/releases/cortx/components/github/${ENV}/rhel-7.7.1908/prod/sspl"
    "/mnt/bigstorage/releases/cortx/github/${ENV}/rhel-7.7.1908"
)

# Allowed Environemnt for the cleanup
ALLOWED_ENV=( "dev" "release" "master" "stable" "main" "cortx-1.0" "custom-ci" "Cortx-v1.0.0_Beta" "pre-cortx-1.0")

# Local Reference 
DO_NOT_REMOVE_DIR=()
OLD_BUILDS=()
BUILDS_FOR_REMOVAL=()

# Validate input argument
_validate_arguments(){

    # Validate the Environment attribute
    if [[ ! " ${ALLOWED_ENV[@]} " =~ " ${ENV} " ]]; then
        echo "Provided environment [ ${ENV} ] is invalid or not in the cleanup list. Exiting..... "
        exit 1
    fi
}

# Find symlink original folder to exclude from cleanup (those symlinks are sprint builds)
_find_protected_builds(){
    echo -e "[ ${ENV} ] | 1. Searching for Protected builds ( release symlink, last ${KEEP_BUILD} build )"
    
    for t_dir in "${TOP_LEVEL_DIR[@]}"; do
        sym_links=$(find -L "$t_dir" -maxdepth 1  -xtype l)
        dir=($(readlink -f "$sym_links"))
        DO_NOT_REMOVE_DIR+=( "${dir[@]}" )  
    done

    for c_dir in "${CLEANUP_DIR[@]}"; do
        if [ -d "$c_dir" ]; then
            dir=( $( ls -trd "${c_dir}/"* | tail -"${KEEP_BUILD}") )
            DO_NOT_REMOVE_DIR+=( "${dir[@]}" ) 
        fi 
    done
    echo -e "\t Do not remove dir count = ${#DO_NOT_REMOVE_DIR[@]}"
}

# Find old builds from the given input path 
_find_old_builds(){
    echo "[ ${ENV} ] | 2. Searching for old builds"
    
    # Cleanup Directory
    echo -e "\t Searching for old builds in given Dir"

    OLD_BUILDS_TEMP=()
    for cleanup_dir in "${CLEANUP_DIR[@]}"; do
        if [ -d "$cleanup_dir" ]; then
            echo -e "\t\t Searching for old builds in $cleanup_dir"
            old_build_in_given_dir=($( { find "$cleanup_dir" -type d -mtime "+${REMOVE_BUILD_OLDER_THEN}" -not -path "*/repodata"; echo; }  | awk 'index($0,prev"/")!=1 && NR!=1 {print prev} 1 {sub(/\/$/,""); prev=$0}'))
            OLD_BUILDS_TEMP+=( "${old_build_in_given_dir[@]}")
        fi
    done

    DEV_SUFFIX="dev"
    PROD_SUFFIX="prod"
    for old_build_tmp in "${OLD_BUILDS_TEMP[@]}"; do

        if [[ "${old_build_tmp}" == *"/${DEV_SUFFIX}" ]];then  
            old_build_tmp=${old_build_tmp%"$DEV_SUFFIX"}
        elif [[ "${old_build_tmp}" == *"/${PROD_SUFFIX}" ]];then
            old_build_tmp=${old_build_tmp%"$PROD_SUFFIX"}
        fi
        OLD_BUILDS+=( "${old_build_tmp}")
    done

    echo -e "\t Total old builds found in the given locations = ${#OLD_BUILDS[@]}"
}

# Exclude protected builds from removal
_get_builds_for_removal(){
    echo "[ ${ENV} ] | 3. Calculating Builds for removal [ Exclude protected builds from cleanup process ]"

    BUILDS_FOR_REMOVAL=()
    for cleanup_build_path in "${OLD_BUILDS[@]}"; do
        ADD_TO_CLEANUP=true
        for protected_build_path in "${DO_NOT_REMOVE_DIR[@]}"; do
            if [[ "${cleanup_build_path}" == "${protected_build_path}"* ]] && [[ "${protected_build_path}" == "${cleanup_build_path}"* ]]; then
                ADD_TO_CLEANUP=false
                break
            fi
        done
        if $ADD_TO_CLEANUP; then
            BUILDS_FOR_REMOVAL+=( "${cleanup_build_path}" )
        fi

    done

    echo -e "\t Builds Going to be deleted  = ${#BUILDS_FOR_REMOVAL[@]}"
    echo -e "\t Total File Size = $(du -csh ${BUILDS_FOR_REMOVAL[@]//} | tail -n 1 | cut -f1)"
}


# Remove builds
_remove_builds(){

    printf '%s\n' "${BUILDS_FOR_REMOVAL[@]}" > "cleanup_$(date +"%Y_%m_%d_%I_%M_%p").txt"
    printf '%s\n' "${DO_NOT_REMOVE_DIR[@]}" > "cleanup_protected_builds_$(date +"%Y_%m_%d_%I_%M_%p").txt"
    
    if [[ "${CLEANUP_MODE}" == "cleanup" ]]; then
        for BUILD in "${BUILDS_FOR_REMOVAL[@]}"; do

            for cleanup_root_path in "${CLEANUP_DIR[@]}"; do
                if [[ "${BUILD}" == "$cleanup_root_path"* ]]; then
                    echo "Removing $BUILD"
                    rm -rf "$BUILD"
                    break
                fi
            done
        done
        echo "[ ${ENV} ] | 4. Build Cleanup Success"
    else
        echo "[ ${ENV} ] | 4. Build Not Cleanedup - Dry-RUN Mode"
    fi 
}

_validate_arguments

_find_protected_builds

_find_old_builds

_get_builds_for_removal

_remove_builds
