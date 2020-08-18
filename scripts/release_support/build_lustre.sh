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

set -eo pipefail

rm -rf lustre
lustre_repo=https://github.com/Cray/lustre.git
lustre_branch=cray-2.12-int
mock_cfg=/etc/mock/lustre/epel-7.7-x86_64.cfg

case "$*" in
    *--use-o2ib*) use_o2ib=true ;;
esac


die() {
    echo >&2 "${0##*/}: ERROR: $*"
    exit 1
}

log() {
    echo "--->  $*"
}

[[ $USER == root ]] ||
    die 'have to be root'

log 'Creating mock config'
mkdir -p ${mock_cfg%/*}
cat > $mock_cfg <<"END_MOCK_CFG"
config_opts['root'] = 'Lustre-7.7-x86_64'
config_opts['target_arch'] = 'x86_64'
config_opts['legal_host_arches'] = ('x86_64',)
config_opts['chroot_setup_cmd'] = 'install @buildsys-build /usr/bin/pigz /usr/bin/lbzip2'
config_opts['dist'] = 'el7'  # only useful for --resultdir variable subst
config_opts['releasever'] = '7'

config_opts['plugin_conf']['root_cache_enable'] = False
config_opts['plugin_conf']['ccache_enable'] = True

config_opts['plugin_conf']['tmpfs_enable'] = False
config_opts['plugin_conf']['tmpfs_opts'] = {}
config_opts['plugin_conf']['tmpfs_opts']['required_ram_mb'] = 1024
config_opts['plugin_conf']['tmpfs_opts']['max_fs_size'] = '24000m'
config_opts['plugin_conf']['tmpfs_opts']['mode'] = '0755'
config_opts['plugin_conf']['tmpfs_opts']['keep_mounted'] = True
config_opts['macros']['%__gzip'] = '/usr/bin/pigz'
config_opts['macros']['%__bzip2'] = '/usr/bin/lbzip2'


config_opts['yum.conf'] = """
[main]
keepcache=1
debuglevel=2
reposdir=/dev/null
logfile=/var/log/yum.log
retries=20
obsoletes=1
gpgcheck=0
assumeyes=1
syslog_ident=mock
syslog_device=
mdpolicy=group:primary
best=1

# repos
[base]
name=BaseOS
baseurl=http://vault.centos.org/7.7.1908/os/x86_64/
failovermethod=priority
gpgkey=file:///usr/share/distribution-gpg-keys/centos/RPM-GPG-KEY-CentOS-7
gpgcheck=0
skip_if_unavailable=False

[updates]
name=updates
baseurl=http://vault.centos.org/7.7.1908/updates/x86_64/
enabled=0
failovermethod=priority
gpgkey=file:///usr/share/distribution-gpg-keys/centos/RPM-GPG-KEY-CentOS-7
gpgcheck=0
skip_if_unavailable=False

[epel]
name=epel
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=epel-7&arch=x86_64
failovermethod=priority
gpgkey=file:///usr/share/distribution-gpg-keys/epel/RPM-GPG-KEY-EPEL-7
gpgcheck=0
skip_if_unavailable=False

[extras]
name=extras
baseurl=http://vault.centos.org/7.7.1908/extras/x86_64/
failovermethod=priority
gpgkey=file:///usr/share/distribution-gpg-keys/centos/RPM-GPG-KEY-CentOS-7
gpgcheck=1
skip_if_unavailable=False

[testing]
name=epel-testing
enabled=0
mirrorlist=http://mirrors.fedoraproject.org/mirrorlist?repo=testing-epel7&arch=x86_64
failovermethod=priority
skip_if_unavailable=False

[mlnx_ofed_4.7]
name=Mellanox Technologies rhel7.7-$basearch mlnx_ofed 4.7
baseurl=https://linux.mellanox.com/public/repo/mlnx_ofed/4.7-3.2.9.0/rhel7.7/x86_64/UPSTREAM_LIBS/
enabled=1
gpgkey=http://www.mellanox.com/downloads/ofed/RPM-GPG-KEY-Mellanox
gpgcheck=0



"""
END_MOCK_CFG

log "Cloning Lustre from $lustre_repo"
git clone --branch $lustre_branch --recursive $lustre_repo

log 'Patching Lustre'
cd lustre
cat > patch <<"END_PATCH"
--- a/LUSTRE-VERSION-GEN
+++ b/LUSTRE-VERSION-GEN
@@ -31,7 +31,7 @@ else
         VC=unset
 fi
 test "$VN" = "$VC" || {
-        echo "LUSTRE_VERSION = $VN" >$LVF
+        echo "LUSTRE_VERSION = $VN" | sed -e 's/cray_//g' -e 's/_dirty//g' >$LVF
 }

-echo $VN
+echo $VN | sed -e 's/cray_//g' -e 's/_dirty//g'
--- a/lustre.spec.in
+++ b/lustre.spec.in
@@ -381,6 +381,18 @@
 clients in order to run
 %endif

+%package devel
+Summary: Lustre include headers
+Group: Development/Kernel
+Provides: %{lustre_name}-devel = %{version}
+Requires: %{requires_kmod_name} = %{requires_kmod_version}
+BuildRequires: rsync
+Conflicts: %{lustre_name}-dkms
+
+%description devel
+This package contains headers required to build ancillary kernel modules that
+work closely with the standard lustre modules.
+
 %if 0%{?suse_version}
 %debug_package
 %endif
@@ -572,6 +584,18 @@
 fi
 %endif

+%define lustre_src_dir %{_prefix}/src/%{lustre_name}-%{version}
+
+:> lustre-devel.files
+mkdir -p $RPM_BUILD_ROOT%{lustre_src_dir}
+cp Module.symvers config.h $RPM_BUILD_ROOT%{lustre_src_dir}
+rsync -a libcfs/include            $RPM_BUILD_ROOT%{lustre_src_dir}/libcfs/
+rsync -a lnet/include              $RPM_BUILD_ROOT%{lustre_src_dir}/lnet/
+rsync -a lustre/include            $RPM_BUILD_ROOT%{lustre_src_dir}/lustre/
+find $RPM_BUILD_ROOT -path "$RPM_BUILD_ROOT%{lustre_src_dir}/*" -fprintf lustre-devel.files '/%%P\n'
+
+%files devel -f lustre-devel.files
+
 %files -f lustre.files
 %defattr(-,root,root)
 %{_sbindir}/*
END_PATCH

git apply patch

log 'Configuring Lustre'
bash autogen.sh
./configure

log 'Generating Lustre srpm'
make srpm


log 'Preparing mock environment'
mock -r ${mock_cfg} clean
mock -r ${mock_cfg} install \
    kernel-3.10.0-1062.el7.x86_64 \
    kernel-devel-3.10.0-1062.el7.x86_64 \
    ${use_o2ib:+mlnx-ofa_kernel-devel}

_KERNEL='3.10.0-1062.el7'
K_ARCH='x86_64'

log "Building Lustre rpms ${use_o2ib:+with o2ib support}"
mock -r ${mock_cfg} --no-clean --rebuild lustre-*.src.rpm \
    --define "kver ${_KERNEL}" \
    --define "kversion ${_KERNEL}.${K_ARCH}" \
    --define "kdir /usr/src/kernels/${_KERNEL}.${K_ARCH}" \
    --with=lnet_dlc \
    --without=servers \
    ${use_o2ib:+--define 'configure_args --with-o2ib=/usr/src/ofa_kernel/default'}

echo
echo '----------------------------------------------------------------'
echo 'Resulting rpms are here: /var/lib/mock/Lustre-7.7-x86_64/result/'
echo '----------------------------------------------------------------'
