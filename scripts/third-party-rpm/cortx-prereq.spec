Name:       cortx-prereq
Version:    %{_cortx_prereq_version}
Release:    %{_release_version}_%{_git_hash}_%{?dist:el7}
Summary:    CORTX pre-requisite package
License:    Seagate

Requires:  third-party-deps
Source:    %{name}-%{version}-%{_git_hash}.tgz

%description
CORTX Depenedecny Package. Installs RPM and Python packages required for CORTX deployment.

%global debug_package %{nil}

%pre
if ! grep -q 'index-url.*python_deps' /etc/pip.conf; then
   echo "ERROR:/etc/pip.conf is not configured with custom python repo. Exiting.."
   echo "Please follow steps mentioned at https://github.com/Seagate/cortx-prvsnr/wiki/Deploy-VM-Hosted-Repo#production-environment"
   exit 1
fi

%prep
%setup -n %{name}-%{version}-%{_git_hash}
rm -rf %{buildroot}

%build

%install
mkdir -p %{buildroot}/opt/seagate/cortx/python-deps
cp -R python_requirements.txt python_requirements.ext.txt %{buildroot}/opt/seagate/cortx/python-deps

%files
/opt/seagate/cortx/python-deps/python_requirements.txt
/opt/seagate/cortx/python-deps/python_requirements.ext.txt

%post
echo -e "\n Installing CORTX prerequisite Python packages. \n"
pip3 install -r /opt/seagate/cortx/python-deps/python_requirements.ext.txt
pip3 install -r /opt/seagate/cortx/python-deps/python_requirements.txt

%clean
rm -rf %{buildroot}

%changelog
# TODO