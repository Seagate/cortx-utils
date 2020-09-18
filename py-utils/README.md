<!--
CORTX-Py-Utils: CORTX Python common library.
Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
## Build
Use setup.py to update the cortx-py-utils distributive.
```bash
python3 setup.py bdist_wheel
```
setup.py is also able to build RPMs. Run
```bash
python3 setup.py bdist_rpm
```
## Installation
Use pip and the wheel file to install the package. E.g.
```bash
cd dist
pip3 install cortx_py_utils-1.0.0-py3-none-any.whl
```
Use pip to uninstall the package
```bash
pip3 uninstall cortx-py-utils
```
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

