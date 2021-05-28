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
# CORTX Python Utilities
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/78aafd1230d04cfb859c3fa5e4d9b030)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Seagate/cortx-py-utils&amp;utm_campaign=Badge_Grade)

A common utils framework which includes common modules across components

<hr>

## Prerequisites for build
```bash
$ sudo yum install gcc
$ sudo yum install rpm-build
$ sudo yum install python36
$ sudo yum install python36-pip
$ sudo yum install python36-devel
$ sudo yum install python36-setuptools
$ sudo yum install openssl-devel
$ sudo yum install libffi-devel
```

## Clone
```
git clone --recursive https://github.com/Seagate/cortx-utils -b main
```


## Build
**Note:** Use one of following method to create build package

  - Create pip package
    - It will create `cortx_py_utils-1.0.0-py3-none-any.whl`
```bash
$ pip3 install wheel
$ cd ./cortx-utils/py-utils
$ python3 setup.py bdist_wheel
```

  - Create RPM Package
It will create `cortx-py-utils-1.0.0-1_<git-version>.noarch.rpm` by default. One can change the version by passing extra `-v <version_string>` parameter.
Below command passes version string as 2.0.0 and build number 2, which creates `cortx-py-utils-2.0.0-2_<git-version>.noarch.rpm`
Run below command from repo root (cortx-utils).
```bash
$ ./jenkins/build.sh -v 2.0.0 -b 2
```

## Installation
  - Installation with pip package
```bash
$ cd ./py-utils/dist
$ pip3 install cortx_py_utils-1.0.0-py3-none-any.whl
```

  - Installation with RPM package
Note : The rpm package installation will fail if any dependent python package is not installed.
Please refer to WIKI (https://github.com/Seagate/cortx-utils/wiki/%22cortx-py-utils%22-single-node-manual-provisioning)
```bash
$ cd ./py-utils/dist
$ yum install -y cortx-py-utils-1.0.0-1.noarch.rpm
```

## Uninstall

- Pip package uninstall
```bash
$ pip3 uninstall cortx-py-utils
```

  - RPM uninstall
```
$ yum remove cortx-py-utils
```

## Update new dependency package

  - Add package in `requirements.txt`.

<hr>

## Usage
After cortx package is installed, it can be used the common way as any other Python module, E.g.:
```python
from cortx.utils.security.cipher import Cipher
```
### Security
#### Cipher
All Cipher methods are static, parameters contain all the neccessary information to perform tasks.

Use `generate_key` method to create an encryption key. The method requires two strings (could be considered
as salt and password), but user can pass more strings if neccessary:
```python
key = Cipher.generate_key('salt','pass','more','strings')
```
Use the obtained key to `encrypt` or `decrypt` your data. Note, that all arguments must be `bytes`:
```python
encrypted = Cipher.encrypt(key, b'secret')
decrypted = Cipher.decrypt(key, encrypted)
```
Note that `decrypt` method might raise a `CipherInvalidToken` exception if the key is not valid.
User might need to handle the exception gracefully if not sure about the key:
```python
try:
    decrypted = Cipher.decrypt(key, encrypted)
except CipherInvalidToken:
    print('Key is wrong')
```
### Utility
#### Validator
The validator modules can be used to perform checks and validate a wide range of things. For example, if a certain service is running, certain packages are installed or not, examine network connectivity etc. For the remote checks, there is an optional hostname usage which will cause ssh connection to remote host, and the ssh must be set up without password beforehand otherwise operation will fail.

  - Package validator: Currently two types of package validators are supported. One for checking rpm packages and the other one for pip3 packages. These APIs can be used to check if certain packages are installed on a remote host as well.

    -- To check if rpm packages are installed, use command "rpms", and pass a list of package names.
```python
from cortx.utils.validator.v_pkg import PkgV
try:
	PkgV().validate('rpms', ["lvm2-2.02.186-7.el7", "openldap-server"])
except Exception as e:
	print("one or more pkgs are not installed on this machine")
```
Note The second example below shows how to check if packages are installed on a remote host specified by "remote_hostname".
```python
	PkgV().validate('rpms', ["lvm2-2.02.186-7.el7", "openldap-server"], "remote_hostname")
```
    -- To check if pip3 packages are installed, use command "pip3", and pass a list of package names.
```python
	PkgV().validate('pip3', ["toml", "salt"])
	PkgV().validate('pip3', ["toml", "salt"], "remote_hostname") # for checking remote pip3 packages
```
  - Service validator: This can be used to check if certain services are running on this host or on a remote host. Use command "isrunning" to check, pass a list of name of services which needs to be checked.
```python
from cortx.utils.validator.v_service import ServiceV
try:
	ServiceV().validate('isrunning', ["rabbitmq-server", "sshd"])
except Exception as e:
	print("one or more services are not running on this machine")
```
Note The second example below shows how to check if given services are running on a remote host specified by "remote_hostname".
```python
	ServiceV().validate('isrunning', ["rabbitmq-server", "sshd"], "remote_hostname")
```
  - Path validator: This can be used to check if certain paths and their types are as expected. Use command "exists" to check, pass a list of colon separated types followed by absolute paths. e.g. ["dir:/", "file:/etc/hosts", "device:/dev/loop9"]
```python
from cortx.utils.validator.v_path import PathV
try:
	PathV().validate('exists', ["dir:/", "file:/etc/hosts", "device:/dev/loop9"])
except Exception as e:
	print("one or more path checks failed")
```
Note The second example below shows how to check if given paths are ok on a remote host specified by "remote_hostname".
```python
	PathV().validate('exists', ["dir:/", "file:/etc/hosts", "device:/dev/loop9"], "remote_hostname")
```
  - Confstore key validator: This can be used to check if an preloaded index on confstore has the requested keys present or not. Use command "exists" to check, pass the preloaded index and a list of 'keys'.
```python
from cortx.utils.validator.v_confkeys import ConfKeysV
try:
	ConfKeysV().validate('exists', index, ['bridge', 'bridge>namei'])
except Exception as e:
	if "key missing" not in f"{e}":
		raise Exception(f"Unexpected exception: {e}")
	print("One or more keys are missing.")
```
