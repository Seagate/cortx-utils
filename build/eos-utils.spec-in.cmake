%define sourcename @CPACK_SOURCE_PACKAGE_FILE_NAME@
%global dev_version %{lua: extraver = string.gsub('@EOS_UTILS_EXTRA_VERSION@', '%-', '.'); print(extraver) }

Name: eos-utils
Version: @EOS_UTILS_BASE_VERSION@
Release: %{dev_version}%{?dist}
Summary: General Purpose Utilities
License: LGPLv3
#Url:
Group: Development/Libraries
Source: %{sourcename}.tar.gz
BuildRequires: cmake gcc
#BuildRequires: @RPM_DEVEL_REQUIRES@
Provides: %{name} = %{version}-%{release}

# Conditionally enable/disable eos-utils options.

%define on_off_switch() %%{?with_%1:ON}%%{!?with_%1:OFF}

# A few explanation about %bcond_with and %bcond_without
# /!\ be careful: this syntax can be quite messy
# %bcond_with means you add a "--with" option, default = without this feature
# %bcond_without adds a"--without" so the feature is enabled by default
@BCOND_FAULT_INJECT@ fault_inject
%global fault_inject %{on_off_switch fault_inject}

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
cmake . -DFAULT_INJECT=%{fault_inject} -DCONFIGURE=OFF \

make %{?_smp_mflags} || make %{?_smp_mflags} || make

%install

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libdir}
mkdir -p %{buildroot}%{_libdir}/pkgconfig
mkdir -p %{buildroot}%{_includedir}/eos/utils/include
install -m 644 include/common.h  %{buildroot}%{_includedir}/eos/utils/include
install -m 644 include/fault.h  %{buildroot}%{_includedir}/eos/utils/include
install -m 744 libeos-utils.so %{buildroot}%{_libdir}
install -m 644 build/eos-utils.pc  %{buildroot}%{_libdir}/pkgconfig

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_libdir}/libeos-utils.so*

%files devel
%defattr(-,root,root)
%{_libdir}/pkgconfig/eos-utils.pc
%{_includedir}/eos/utils/include/common.h
%{_includedir}/eos/utils/include/fault.h

%changelog
