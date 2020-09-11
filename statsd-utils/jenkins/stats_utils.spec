Name: stats_utils
Version: %{version}
Release: %{_build_number}_%{dist}
Summary: STATS Tools
License: Seagate Proprietary
Requires: statsd
URL: http://gitlab.mero.colo.seagate.com/third_party/statsd-utils
Source0: statsd-utils-%{version}.tar.gz
%define debug_package %{nil}

%description
STATS Tools

%prep
%setup -n statsd-utils
# Nothing to do here

%build

%install
mkdir -p ${RPM_BUILD_ROOT}/opt/statsd-utils
cp -rp . ${RPM_BUILD_ROOT}/opt/statsd-utils
exit 0

%post
cp -rf /opt/statsd-utils/statsd-elasticsearch-backend-0.4.2/config.js /etc/statsd/
exit 0

%postun
exit 0

%clean

%files
%defattr(-, root, root, -)
/opt/statsd-utils/*

%changelog
* Fri Dec 20 2019 Ajay Paratmandali <ajay.paratmandali@seagate.com> - 1.0.0
- Initial spec file
