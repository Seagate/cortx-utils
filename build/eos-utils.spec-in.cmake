%define sourcename @CPACK_SOURCE_PACKAGE_FILE_NAME@
%global dev_version %{lua: extraver = string.gsub('@EOS_UTILS_EXTRA_VERSION@', '%-', '.'); print(extraver) }

Name: eos-utils
Version: @EOS_UTILS_BASE_VERSION@
Release: %{dev_version}%{?dist}
Summary: General Purpose Utilities
License: Seagate
#Url:
Group: Development/Libraries
Source: %{sourcename}.tar.gz
BuildRequires: cmake gcc
#BuildRequires: @RPM_DEVEL_REQUIRES@
Provides: %{name} = %{version}-%{release}

# EOS UTILS library paths
%define _utils_dir		@INSTALL_DIR_ROOT@/@PROJECT_NAME_BASE@/utils
%define _utils_lib_dir		%{_utils_dir}/lib
%define _utils_include_dir	%{_includedir}/@PROJECT_NAME_BASE@-utils

# Conditionally enable/disable eos-utils options.
%define on_off_switch() %%{?with_%1:ON}%%{!?with_%1:OFF}

# A few explanation about %bcond_with and %bcond_without
# /!\ be careful: this syntax can be quite messy
# %bcond_with means you add a "--with" option, default = without this feature
# %bcond_without adds a"--without" so the feature is enabled by default
@BCOND_FAULT_INJECT@ fault_inject
%global fault_inject %{on_off_switch fault_inject}

@BCOND_ENABLE_DASSERT@ enable_dassert
%global enable_dassert %{on_off_switch enable_dassert}

%description
The libutils is the container to hold all the general purpose libraries.
Libraries like - fault, log etc...

%package devel
Summary: Development file for the libutils
Group: Development/Libraries
Requires: %{name} = %{version}-%{release} pkgconfig
#Requires: @RPM_DEVEL_REQUIRES@
Provides: %{name}-devel = %{version}-%{release}

%description devel
The libutils is the container to hold all the general purpose libraries.

%prep
%setup -q -n %{sourcename}

%build
cmake . -DFAULT_INJECT=%{fault_inject} \
	-DENABLE_DASSERT=%{enable_dassert} \
	-DCONFIGURE=OFF

make %{?_smp_mflags} || make %{?_smp_mflags} || make

%install

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_utils_dir}
mkdir -p %{buildroot}%{_utils_lib_dir}
mkdir -p %{buildroot}%{_utils_include_dir}/
mkdir -p %{buildroot}%{_utils_include_dir}/eos
mkdir -p %{buildroot}%{_utils_include_dir}/common
mkdir -p %{buildroot}%{_libdir}/pkgconfig
install -m 644 include/*.h  %{buildroot}%{_utils_include_dir}
install -m 644 include/eos/*.h  %{buildroot}%{_utils_include_dir}/eos
install -m 644 include/common/*.h  %{buildroot}%{_utils_include_dir}/common
install -m 755 libeos-utils.so %{buildroot}%{_utils_lib_dir}
install -m 644 build/eos-utils.pc  %{buildroot}%{_libdir}/pkgconfig
ln -s %{_utils_lib_dir}/libeos-utils.so %{buildroot}%{_libdir}/libeos-utils.so

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_libdir}/libeos-utils.so*
%{_utils_lib_dir}/libeos-utils.so*

%files devel
%defattr(-,root,root)
%{_libdir}/pkgconfig/eos-utils.pc
%{_utils_include_dir}/*.h
%{_utils_include_dir}/eos/*.h
%{_utils_include_dir}/common/*.h

%changelog
