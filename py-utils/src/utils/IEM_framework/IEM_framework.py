#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

class IEM:
    severity=" "
    source_id=" "
    component_id=None
    module_id=None
    event_id=None
    message=" "
    params={1:'cause1'
            2:'cause2'
            3:'cause3' }

    def __init__(self):
    
    def __init__(self,severity:str, source_id:str, component_id,module_id,event_id,message:str,**params):
        self..sevrity=severity
        self.source_id=source_id
        self.component_id=component_id
        self.module_id=module_id
        self.event_id=event_id
        self.message=message
        self.params=params

    def populate(self,severity:str, source_id:str, component_id, module_id, event_id, message:str,**params):
        self.severity=severity
        self.source_id=source_id
        self.component_id=component_id
        self.module_id=module_id
        self.event_id=event_id
        self.message=message
        self.params=params

    def print_IEM(self):
        print(" source_id : "+ self.source_id+" component_id : "+self.component_id+ " module_id : "+self.module_id)
        print("severity : "+self.severity)
        print("Reporting error is %s",self.message)
        for key in self.params:
            print key,self.params[key]
