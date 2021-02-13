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

from  cortx.utils.IEM_framework import IEM

class IEM_Producer:
    """ A class that produce the IEM alerts """
    cluster_id=None
    site_id=None
    rack_id=None    
    node_id=None
        
    def ___init__(self,cluster_id,site_id,rack_id,node_id):
        self.cluster_id=cluster_id
        self.site_id=site_id
        self.rack_id=rack_id
        self.node_id=node_id

    """ Intialize the Producer class 
        Parameters :
        site_id  HEX number that represents the data center site
        rack_id  Hex value that identify the a single rack in a single site
        node_id  Hex number that represents the type of node in a cluster 
    """ 
    def send(self,iem:IEM):
        return self.send(iem)
