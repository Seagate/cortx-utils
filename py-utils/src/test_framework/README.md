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

# Cortx-Py-Utils Test Framework for Unittests

---

## Clone

```bash
git clone https://github.com/Seagate/cortx-utils.git
```

## Prerequisite for running tests

1.  cortx-py-utils, Kafka server and cortx-py-utils-test must be installed, if not please follow [Link](https://github.com/Seagate/cortx-utils/blob/main/py-utils/test/README.md)

## Procedure to run tests

*   Running tests from entrypoint by passing path of a plan
```bash
run_test -c <cluster.conf path> -t /usr/lib/python3.6/site-packages/cortx/utils/test/plans/<plan_name>.pln
```

*   Running tests through utils_setup Test phase by passing plan name
```bash
/opt/seagate/cortx/utils/bin/utils_setup test --config <cluster.conf path> --plan <plan_name>
```

*   Running tests through executable file run_test by passing path of a plan
```bash
/opt/seagate/cortx/utils/bin/run_test -c <cluster.conf path> -t /usr/lib/python3.6/site-packages/cortx/utils/test/plans/<plan_name>.pln
```

**Note:** Here, `<plan_name>.pln` should exist in plans directory under /py-utils/test, i.e, `cortx-utils/py-utils/test/plans/`

## Test command structure in <plane_name>.pln file

*   To run a single test
```bash
<directory_name>.<test_file_name>.<class_name>.<test_name>
```
> Ex: conf_store.test_conf_cli.TestConfCli.test_conf_cli_properties_wrong_format_kv

*   To run all the tests from a test_file.py
```bash
<directory_name>.<test_file_name>
```
> Ex: conf_store.test_conf_cli

**Note:** Here, `<plane_name>.pln` file can have a combination of both the test command structures. Directory_name is the name of directories under /py-utils/test
