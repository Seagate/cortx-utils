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

1. cortx-py-utils must be installed, if not follow [Link](https://github.com/Seagate/cortx-utils/blob/main/py-utils/README.md "cortx-py-utils installation").
2. Kafka service up and running, if not follow [Link](https://github.com/Seagate/cortx-utils/wiki/Kafka-Server-Setup "Kafka installation")

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
sudo yum install dist/cortx_test-1.0.0-1.noarch.rpm
```

- Install with pip package

```bash
sudo pip3 install dist/cortx_test-1.0.0-py3-none-any.whl
```

### Uninstall

- RPM uninstall

```bash
yum remove cortx-test
```

- Pip package uninstall

```bash
pip3 uninstall cortx_test
```

