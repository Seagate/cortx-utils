%define sourcename @CPACK_SOURCE_PACKAGE_FILE_NAME@
%global dev_version %{lua: extraver = string.gsub('@CORTX_UTILS_EXTRA_VERSION@', '%-', '.'); print(extraver) }

Name: @PROJECT_NAME@
Version: @CORTX_UTILS_BASE_VERSION@
Release: %{dev_version}%{?dist}
Summary: General Purpose Utilities
URL: GHS://@PROJECT_NAME@
License: Seagate
#Url:
Group: Development/Libraries
Source: %{sourcename}.tar.gz
BuildRequires: cmake gcc
#BuildRequires: @RPM_DEVEL_REQUIRES@
Requires: python36-toml
Provides: %{name} = %{version}-%{release}

# CORTX UTILS library paths
%define _utils_lib		@PROJECT_NAME@
%define _utils_dir		@INSTALL_DIR_ROOT@/@PROJECT_NAME_BASE@/utils
%define _utils_lib_dir		%{_utils_dir}/lib
%define _utils_include_dir	%{_includedir}/@PROJECT_NAME_BASE@-utils

# Conditionally enable/disable cortx-utils options.
%define on_off_switch() %%{?with_%1:ON}%%{!?with_%1:OFF}

# A few explanation about %bcond_with and %bcond_without
# /!\ be careful: this syntax can be quite messy
# %bcond_with means you add a "--with" option, default = without this feature
# %bcond_without adds a"--without" so the feature is enabled by default
@BCOND_FAULT_INJECT@ fault_inject
%global fault_inject %{on_off_switch fault_inject}

@BCOND_ENABLE_DASSERT@ enable_dassert
%global enable_dassert %{on_off_switch enable_dassert}

@BCOND_ENABLE_TSDB_ADDB@ enable_tsdb_addb
%global enable_tsdb_addb%{on_off_switch enable_tsdb_addb}

%description
The @PROJECT_NAME@ is the container to hold all the general purpose libraries.
Libraries like - fault, log etc...

%package devel
Summary: Development file for the @PROJECT_NAME@
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} pkgconfig
#Requires: @RPM_DEVEL_REQUIRES@
Provides: %{name}-devel = %{version}-%{release}

%description devel
The @PROJECT_NAME@ is the container to hold all the general purpose libraries.

%prep
%setup -q -n %{sourcename}

%build
cmake . -DFAULT_INJECT=%{fault_inject} \
	-DENABLE_DASSERT=%{enable_dassert} \
	-DENABLE_TSDB_ADDB=%{enable_tsdb_addb} \
	-DPROJECT_NAME_BASE=@PROJECT_NAME_BASE@ \
	-DCONFIGURE=OFF

make %{?_smp_mflags} || make %{?_smp_mflags} || make

%install

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_utils_dir}
mkdir -p %{buildroot}%{_utils_lib_dir}
mkdir -p %{buildroot}%{_utils_include_dir}/
mkdir -p %{buildroot}%{_utils_include_dir}/cortx
mkdir -p %{buildroot}%{_utils_include_dir}/common
mkdir -p %{buildroot}%{_libdir}/pkgconfig
install -m 644 include/*.h  %{buildroot}%{_utils_include_dir}
install -m 644 include/cortx/*.h  %{buildroot}%{_utils_include_dir}/cortx
install -m 644 include/common/*.h  %{buildroot}%{_utils_include_dir}/common
install -m 755 lib%{_utils_lib}.so %{buildroot}%{_utils_lib_dir}
install -m 644 build/%{_utils_lib}.pc  %{buildroot}%{_libdir}/pkgconfig
ln -s %{_utils_lib_dir}/lib%{_utils_lib}.so %{buildroot}%{_libdir}/lib%{_utils_lib}.so

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_libdir}/lib%{_utils_lib}.so*
%{_utils_lib_dir}/lib%{_utils_lib}.so*

%files devel
%defattr(-,root,root)
%{_libdir}/pkgconfig/%{_utils_lib}.pc
%{_utils_include_dir}/*.h
%{_utils_include_dir}/cortx/*.h
%{_utils_include_dir}/common/*.h

%changelog
* Tue Jun 16 2020 Seagate 1.0.1
- RPM Naming Convention.
