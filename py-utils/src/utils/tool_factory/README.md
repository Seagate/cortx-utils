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

## Get the Utility

```bash
curl -OL https://raw.githubusercontent.com/Seagate/cortx-utils/kubernetes/py-utils/src/utils/tool_factory/extract_support_bundle.sh
```

### Procedure to extract SB

*   Execute extract_support_bundle.sh script from entrypoint passing args:
    | Flag short | Description | Default |
    | --- | --- | --- |
    | -f | absolute file path of SB archive |
    | -d | destination path to extract the SB| $PWD |
    | -c | components_list as a string seperated by comma| "all" |

#### Example Command
```bash
./extract_support_bundle.sh \
-f 'SB09995_8d00f71d6e0eeef02e971e6356bb83aa.tar.gz' \
-d '~/support_bundle' \
-c "common, utils"
```