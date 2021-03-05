Name:       cortx-prereq
Version:    %{_cortx_prereq_version}
Release:    %{_release_version}_%{_git_hash}_%{?dist:el7}
Summary:    CORTX pre-requisite package
License:    Seagate

Requires:  third-party-deps
Source:    %{name}-%{version}-%{_git_hash}.tgz

%description
CORTX Depenedecny Package

%global debug_package %{nil}

%prep
%setup -n %{name}-%{version}-%{_git_hash}
rm -rf %{buildroot}

%build

%install
mkdir -p %{buildroot}/opt/seagate/cortx/python-deps
cp -R python-requirements.txt %{buildroot}/opt/seagate/cortx/python-deps

%files
/opt/seagate/cortx/python-deps/python-requirements.txt

%post
echo -e "\n Installing CORTX prerequisite Python packages. \n"
pip3 install -r /opt/seagate/cortx/python-deps/python-requirements.txt

%clean
rm -rf %{buildroot}

%changelog
# TODO
