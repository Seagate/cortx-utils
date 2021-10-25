<!--                                                                            
Tool Factory: CORTX Python common tool library.                                    
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

# Support Bundle Extractor Utility

---

## Clone -> Get the Utility

```bash
git clone https://github.com/Seagate/cortx-utils.git
cd cortx-utils/py-utils/src/utils/tool_factory
```

### Procedure to extract SB

*   Execute extract_support_bundle.sh script from entrypoint passing args:
<file_path of tar archive> <destination> [Optional Parameter, Default: $PWD]
<components_list as a string seperated by comma> [Optional Parameter, Default: "All components"]

#### Example Command
```bash
<install_path>/py-utils/src/utils/tool_factory/extract_support_bundle.sh
-f '/tmp/SB09995_8d00f71d6e0eeef02e971e6356bb83aa.tar.gz'
-d '/var/cortx/support_bundle' -c "common, utils"
```
