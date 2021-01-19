# build number
%define u_build_num  %(test -n "$build_number" && echo "$build_number" || echo 1)

Name: cortx-py-utils
Version: %{u_version}
Release: %{u_build_num}_%{u_gitrev}%{?dist}
Summary: cortx-py-utils (common utilities)

Group: System Environment
License: Seagate
URL: https://github.com/Seagate/cortx-py-utils
Source: %{name}-1.0.0.tar.gz

BuildRequires: binutils-devel
BuildRequires: git
BuildRequires: python36
BuildRequires: python36-devel
BuildRequires: python36-pip
BuildRequires: python36-setuptools

Requires: python36

%description
Cortx common utilities required by various components.

%prep
%setup -qn %{name}


%build
make %{?_smp_mflags}


%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
sed -i -e 's@^#!.*\.py3venv@#!/usr@' %{buildroot}/opt/seagate/cortx/utils/bin/*


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
/opt/seagate/cortx/utils/*


# Don't fail if /usr/lib/rpm/brp-python-bytecompile reports syntax errors --
# that script doesn't work with python3.
# FIXME: https://github.com/scylladb/scylla/issues/2235 suggests that proper
# fix is to rename all *.py files to *.py3.
%define _python_bytecompile_errors_terminate_build 0

%post
opt_usr_lib=/opt/seagate/cortx/utils/lib/python3.6/site-packages
opt_usr_lib64=/opt/seagate/cortx/utils/lib64/python3.6/site-packages

usr_lib_dirs=$(cd $opt_usr_lib && find . -maxdepth 1 -type d | cut -d'/' -f2)
usr_lib64_dirs=$(cd $opt_usr_lib64 && find . -maxdepth 1 -type d | cut -d'/' -f2)
usr_lib_files=$(cd $opt_usr_lib && find . -maxdepth 1 -type f | cut -d'/' -f2)
usr_lib64_files=$(cd $opt_usr_lib64 && find . -maxdepth 1 -type f | cut -d'/' -f2)

for d in $usr_lib_dirs; do
    if [[ ! -d /usr/lib/python3.6/site-packages/$d ]]; then
        ln -s /opt/seagate/cortx/utils/lib/python3.6/site-packages/$d /usr/lib/python3.6/site-packages/
    fi
done
for f in $usr_lib_files; do
    if [[ ! -f /usr/lib/python3.6/site-packages/$f ]]; then
        ln -s /opt/seagate/cortx/utils/lib/python3.6/site-packages/$f /usr/lib/python3.6/site-packages/
    fi
done
for d in $usr_lib64_dirs; do
    if [[ ! -d /usr/lib64/python3.6/site-packages/$d ]]; then
        ln -s /opt/seagate/cortx/utils/lib64/python3.6/site-packages/$d /usr/lib64/python3.6/site-packages/
    fi
done
for f in $usr_lib64_files; do
    if [[ ! -f /usr/lib64/python3.6/site-packages/$f ]]; then
        ln -s /opt/seagate/cortx/utils/lib64/python3.6/site-packages/$f /usr/lib64/python3.6/site-packages/
    fi
done
