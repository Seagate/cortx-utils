#!/bin/bash
###############################################################################
# Build script for EOS_UTILS component.
###############################################################################
set -e

###############################################################################
# Arguments

# Project Name.
PROJECT_NAME_BASE=${PROJECT_NAME_BASE:-"cortx"}

# Install Dir.
INSTALL_DIR_ROOT=${INSTALL_DIR_ROOT:-"/opt/seagate"}

# EOS-UTILS source repo root.
EOS_UTILS_SOURCE_ROOT=${EOS_UTILS_SOURCE_ROOT:-$PWD}

# Root folder for out-of-tree builds, i.e. location for the build folder.
# For superproject builds: it is derived from EOS_UTILS_BUILD_ROOT (utils/build-eos_utils).
# For local builds: it is based on $PWD (./build-eos_utils).
EOS_UTILS_CMAKE_BUILD_ROOT=${EOS_FS_BUILD_ROOT:-$EOS_UTILS_SOURCE_ROOT}

# Select EOS_UTILS Source Version.
# Superproject: derived from eos-utils version.
# Local: taken fron VERSION file.
EOS_UTILS_VERSION=${EOS_UTILS_VERSION:-"$(cat $EOS_UTILS_SOURCE_ROOT/VERSION)"}


# Select EOS-UTILS Build Version.
# Superproject: derived from eos-utils version.
# Local: taken from git rev.
EOS_UTILS_BUILD_VERSION=${EOS_FS_BUILD_VERSION:-"$(git rev-parse --short HEAD)"}

###############################################################################
# Local variables

FAULT_INJECTION="ON"

case $FAULT_INJECTION in
    "ON")
        FAULT_INJECT="ON" ;;
    "OFF")
        FAULT_INJECT="OFF" ;;
    *)
        echo "Invalid Fault Injection configuration $FAULT_INJECTION"
        exit 1;;
esac

EOS_UTILS_BUILD=$EOS_UTILS_CMAKE_BUILD_ROOT/build-eos-utils
EOS_UTILS_SRC=$EOS_UTILS_SOURCE_ROOT/src

###############################################################################
eos_utils_print_env() {
    myenv=(
        EOS_UTILS_SOURCE_ROOT
        EOS_UTILS_CMAKE_BUILD_ROOT
        EOS_UTILS_VERSION
        EOS_UTILS_BUILD_VERSION
        EOS_UTILS_BUILD
        EOS_UTILS_SRC
	FAULT_INJECT
    )

    for i in ${myenv[@]}; do
        echo "$i=${!i}"
    done
}

###############################################################################
eos_utils_configure() {
    if [ -f $EOS_UTILS_BUILD/.config ]; then
        echo "Build folder exists. Please remove it."
        exit 1;
    fi

    mkdir $EOS_UTILS_BUILD
    cd $EOS_UTILS_BUILD

    local cmd="cmake \
-DFAULT_INJECT=${FAULT_INJECT} \
-DENABLE_DASSERT=${ENABLE_DASSERT} \
-DCONFIGURE=ON \
-DBASE_VERSION:STRING=${EOS_UTILS_VERSION} \
-DRELEASE_VER:STRING=${EOS_UTILS_BUILD_VERSION} \
-DPROJECT_NAME_BASE:STRING=${PROJECT_NAME_BASE} \
-DINSTALL_DIR_ROOT:STRING=${INSTALL_DIR_ROOT}
$EOS_UTILS_SRC"
    echo -e "Config:\n $cmd" > $EOS_UTILS_BUILD/.config
    echo -e "Env:\n $(eos_utils_print_env)" >> $EOS_UTILS_BUILD/.config
    $cmd
    cd -
}

###############################################################################
eos_utils_make() {
    if [ ! -d $EOS_UTILS_BUILD ]; then
        echo "Build folder does not exist. Please run 'config'"
        exit 1;
    fi

    cd $EOS_UTILS_BUILD
    make "$@"
    cd -
}

###############################################################################
eos_utils_purge() {
    if [ ! -d "$EOS_UTILS_BUILD" ]; then
        echo "Nothing to remove"
        return 0;
    fi

    rm -fR "$EOS_UTILS_BUILD"
}

###############################################################################
eos_utils_jenkins_build() {
    eos_utils_print_env && \
        eos_utils_purge && \
        eos_utils_configure && \
        eos_utils_make all links rpms && \
        eos_utils_make clean
        eos_utils_purge
}

###############################################################################
eos_utils_rpm_gen() {
    eos_utils_make  rpms
}

eos_utils_rpm_install() {
    local rpms_dir=$HOME/rpmbuild/RPMS/x86_64
    local dist=$(rpm --eval '%{dist}')
    local suffix="${EOS_UTILS_VERSION}-${EOS_UTILS_BUILD_VERSION}${dist}.x86_64.rpm"
    local mypkg=(
        ${PROJECT_NAME_BASE}-utils
        ${PROJECT_NAME_BASE}-utils-debuginfo
        ${PROJECT_NAME_BASE}-utils-devel
    )
    local myrpms=()

    for pkg in ${mypkg[@]}; do
        local rpm_file=$rpms_dir/$pkg-$suffix
        if [ ! -f $rpm_file ]; then
            echo "Cannot find RPM file for package "$pkg" ('$rpm_file')"
            return 1
        else
            myrpms+=( $rpm_file )
        fi
    done

    echo "Installing the following RPMs:"
    for rpm in ${myrpms[@]}; do
        echo "$rpm"
    done

    sudo yum install -y ${myrpms[@]}
    local rc=$?

    echo "Done ($rc)."
    return $rc
}

eos_utils_rpm_uninstall() {
    sudo yum remove -y "${PROJECT_NAME_BASE}-utils*"
}

eos_utils_reinstall() {
    eos_utils_rpm_gen &&
        eos_utils_rpm_uninstall &&
        eos_utils_rpm_install &&
    echo "OK"
}

###############################################################################
eos_utils_usage() {
    echo -e "
EOS-UTILS Build script.
Usage:
    env <build environment> $0 <action>

Where action is one of the following:
        help    - Print usage.
        env     - Show build environment.
        jenkins - Run automated CI build.

        config  - Run configure step.
        purge   - Clean up all files generated by build/config steps.
        reconf  - Clean up build dir and run configure step.

        make    - Run make [...] command.

        reinstall - Build RPMs, remove old pkgs and install new pkgs.
        rpm-gen - Build RPMs.
        rpm-install - Install RPMs build by rpm-gen.
        rpm-uninstall - Uninstall pkgs.

        test    - Run all EOS-UTILS functional tests from the build folder.

An example of a typical workflow:
    $0 config -- Generates out-of-tree cmake build folder.
    $0 make -j -- Compiles files in it.
    $0 reinstall -- Generates and re-installs RPMs.
"
}

###############################################################################
case $1 in
    env)
        eos_utils_print_env;;
    jenkins)
        eos_utils_jenkins_build;;
    config)
        eos_utils_configure;;
    reconf)
        eos_utils_purge && eos_utils_configure;;
    purge)
        eos_utils_purge;;
    make)
        shift
        eos_utils_make "$@" ;;
    rpm-gen)
        eos_utils_rpm_gen;;
    rpm-install)
        eos_utils_rpm_install;;
    rpm-uninstall)
        eos_utils_rpm_uninstall;;
    reinstall)
        eos_utils_reinstall;;
    *)
        eos_utils_usage;;
esac

###############################################################################
