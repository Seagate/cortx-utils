#!/bin/bash
###############################################################################
# Build script for CORTX_UTILS component.
###############################################################################
set -e

###############################################################################
# Arguments

# Project Name.
PROJECT_NAME_BASE=${PROJECT_NAME_BASE:-"cortx"}

# Install Dir.
INSTALL_DIR_ROOT=${INSTALL_DIR_ROOT:-"/opt/seagate"}

# CORTX-UTILS source repo root.
CORTX_UTILS_SOURCE_ROOT=${CORTX_UTILS_SOURCE_ROOT:-$PWD}

# Root folder for out-of-tree builds, i.e. location for the build folder.
# For superproject builds: it is derived from CORTX_UTILS_BUILD_ROOT (utils/build-cortx_utils).
# For local builds: it is based on $PWD (./build-cortx_utils).
CORTX_UTILS_CMAKE_BUILD_ROOT=${CORTXFS_BUILD_ROOT:-$CORTX_UTILS_SOURCE_ROOT}

# Select CORTX_UTILS Source Version.
# Superproject: derived from cortx-utils version.
# Local: taken fron VERSION file.
UTILS_VERSION=$(cat "$CORTX_UTILS_SOURCE_ROOT/VERSION")
CORTX_UTILS_VERSION=${CORTX_UTILS_VERSION:-"$UTILS_VERSION"}

# Select CORTX-UTILS Build Version.
# Taken from git rev of UTILS repo
GIT_DIR="$CORTX_UTILS_SOURCE_ROOT/../.git"
CORTX_UTILS_BUILD_VERSION="$(git --git-dir "$GIT_DIR" rev-parse --short HEAD)"

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

CORTX_UTILS_BUILD=$CORTX_UTILS_CMAKE_BUILD_ROOT/build-cortx-utils
CORTX_UTILS_SRC=$CORTX_UTILS_SOURCE_ROOT/src

###############################################################################
cortx_utils_print_env() {
    myenv=(
        CORTX_UTILS_SOURCE_ROOT
        CORTX_UTILS_CMAKE_BUILD_ROOT
        CORTX_UTILS_VERSION
        CORTX_UTILS_BUILD_VERSION
        CORTX_UTILS_BUILD
        CORTX_UTILS_SRC
	FAULT_INJECT
    )

    for i in ${myenv[@]}; do
        echo "$i=${!i}"
    done
}

###############################################################################
cortx_utils_configure() {
    if [ -f "$CORTX_UTILS_BUILD/.config" ]; then
        echo "Build folder exists. Please remove it."
        exit 1;
    fi

    mkdir "$CORTX_UTILS_BUILD"
    cd "$CORTX_UTILS_BUILD"

    local cmd="cmake \
-DFAULT_INJECT=${FAULT_INJECT} \
-DENABLE_DASSERT=${ENABLE_DASSERT} \
-DCONFIGURE=ON \
-DBASE_VERSION:STRING=${CORTX_UTILS_VERSION} \
-DRELEASE_VER:STRING=${CORTX_UTILS_BUILD_VERSION} \
-DPROJECT_NAME_BASE:STRING=${PROJECT_NAME_BASE} \
-DINSTALL_DIR_ROOT:STRING=${INSTALL_DIR_ROOT}"

    echo -e "Config:\n $cmd" > "$CORTX_UTILS_BUILD/.config"
    echo -e "Env:\n $(cortx_utils_print_env)" >> "$CORTX_UTILS_BUILD/.config"
    $cmd "$CORTX_UTILS_SRC"
    cd -
}

###############################################################################
cortx_utils_make() {
    if [ ! -d "$CORTX_UTILS_BUILD" ]; then
        echo "Build folder does not exist. Please run 'config'"
        exit 1;
    fi

    cd "$CORTX_UTILS_BUILD"
    make "$@"
    cd -
}

###############################################################################
cortx_utils_purge() {
    if [ ! -d "$CORTX_UTILS_BUILD" ]; then
        echo "Nothing to remove"
        return 0;
    fi

    rm -fR "$CORTX_UTILS_BUILD"
}

###############################################################################
cortx_utils_jenkins_build() {
    cortx_utils_print_env && \
        cortx_utils_purge && \
        cortx_utils_configure && \
        cortx_utils_make all links rpms && \
        cortx_utils_make clean
        cortx_utils_purge
}

###############################################################################
cortx_utils_rpm_gen() {
    cortx_utils_make  rpms
}

cortx_utils_rpm_install() {
    local rpms_dir=$HOME/rpmbuild/RPMS/x86_64
    local dist=$(rpm --eval '%{dist}')
    local suffix="${CORTX_UTILS_VERSION}-${CORTX_UTILS_BUILD_VERSION}${dist}.x86_64.rpm"
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

cortx_utils_rpm_uninstall() {
    sudo yum remove -y "${PROJECT_NAME_BASE}-utils*"
}

cortx_utils_reinstall() {
    cortx_utils_rpm_gen &&
        cortx_utils_rpm_uninstall &&
        cortx_utils_rpm_install &&
    echo "OK"
}

###############################################################################
cortx_utils_usage() {
    echo -e "
CORTX-UTILS Build script.
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

        test    - Run all CORTX-UTILS functional tests from the build folder.

An example of a typical workflow:
    $0 config -- Generates out-of-tree cmake build folder.
    $0 make -j -- Compiles files in it.
    $0 reinstall -- Generates and re-installs RPMs.
"
}

###############################################################################
case $1 in
    env)
        cortx_utils_print_env;;
    jenkins)
        cortx_utils_jenkins_build;;
    config)
        cortx_utils_configure;;
    reconf)
        cortx_utils_purge && cortx_utils_configure;;
    purge)
        cortx_utils_purge;;
    make)
        shift
        cortx_utils_make "$@" ;;
    rpm-gen)
        cortx_utils_rpm_gen;;
    rpm-install)
        cortx_utils_rpm_install;;
    rpm-uninstall)
        cortx_utils_rpm_uninstall;;
    reinstall)
        cortx_utils_reinstall;;
    *)
        cortx_utils_usage;;
esac

###############################################################################
