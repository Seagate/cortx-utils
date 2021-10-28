<!--                                                                            
CORTX-Py-Utils: CORTX Python common library.                                    
Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates                 
This program is free software: you can redistribute it and/or modify            
it under the terms of the GNU Affero General Public License as published        
by the Free Software Foundation, either version 3 of the License, or            
(at your option) any later version.                                             
This program is distributed in the hope that it will be useful,                 
but WITHOUT ANY WARRANTY; without even the implied warranty of                  
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the                    
GNU Affero General Public License for more details.                             
You should have received a copy of the GNU Affero General Public License        
along with this program. If not, see <https://www.gnu.org/licenses/>.           
For any questions about this software or licensing,                             
please email opensource@seagate.com or cortx-questions@seagate.com.             
-->

# Cortx-Py-Utils Test rpm

---

## Prerequisite for Test-Rpm build

1. Install cortx-py-utils

> Follow [cortx-py-utils installtion guide](https://github.com/Seagate/cortx-utils/blob/main/py-utils/README.md "cortx-py-utils installation")

2.  cortx-py-utils mini-provisioning

> For single node, follow [single node mini provisioning](https://github.com/Seagate/cortx-utils/wiki/%22cortx-py-utils%22-single-node-manual-provisioning "single node mini provisioning")

> For multi node, follow [multi node mini provisioning](https://github.com/Seagate/cortx-utils/wiki/cortx-py-utils-multi-node-manual-provisioning "multi node mini provisioning")

### Clone

```bash
git clone https://github.com/Seagate/cortx-utils.git
```

### Build

**Note:** Use one of following method to create build package

- Create RPM package

```bash
# NOTE: Do not use rpm if cortx-py-utils is installed using wheel & pip
cd cortx-utils/py-utils/test
sudo python3 setup.py bdist_rpm  --requires cortx-py-utils --version=1.0.0 --post-install test-post-install --post-uninstall test-post-uninstall
```

- Create pip Package

```bash
cd cortx-utils/py-utils/test
sudo python3 setup.py bdist_wheel --version=1.0.0
```

> both wheel or rpm gets copied under "/py-utils/test/dist " directory

### Install

- Install with RPM package

```sh
sudo yum install dist/cortx-py-utils-test-1.0.0-1.noarch.rpm
```

- Install with pip package

```bash
sudo pip3 install dist/cortx-py-utils-test-1.0.0-py3-none-any.whl
```

### Uninstall

- RPM uninstall

```bash
yum remove cortx_test
```

- Pip package uninstall

```bash
pip3 uninstall cortx_test
```

---

## Run py-utils unittests without Test-RPM

### Clone cortx-utils repo

```bash
git clone https://github.com/Seagate/cortx-utils.git
```

### To run all the unittests in py-utils

-   Go to py-utils/test directory and execute below command:

```bash
python3 -m unittest discover
```

**Note:** Some of the py-utils unittests are dependent on other cortx components, If cortx-py-utils is deployed alone, then some test cases will not succeed such as validator, support_bundle etc.

### To run all the unittests from a test file

-   Go to the respective feature directory under py-utils/test and execute below command:

```bash
python3 test_file.py
```

### To run a single unittest from a test file

-   Go to the respective feature directory under py-utils/test and execute below command:

```bash
python3 -m unittest test_module.TestClass.test_method
```

**Disclaimer:** py-utils unittests from the below test scripts will do SSH to localhost, node, hostname to verify the py-utils functionalities

```bash
cortx-utils/py-utils/test/test_ssh_connection.py
cortx-utils/py-utils/test/validator/test_bmc_validator.py
cortx-utils/py-utils/test/validator/test_consul_validator.py
cortx-utils/py-utils/test/validator/test_controller_validator.py
cortx-utils/py-utils/test/validator/test_network_validator.py
cortx-utils/py-utils/test/validator/test_path_validator.py
cortx-utils/py-utils/test/validator/test_service_validator.py
```
