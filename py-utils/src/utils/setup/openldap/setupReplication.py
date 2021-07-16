#!/usr/bin/env python3
#
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

import sys
import os
import ldap
import ldap.modlist as modlist
import shutil
import glob
from shutil import copyfile
import socket
from cortx.utils.log import Log

class Replication:
    hostlist = []
    Log.init('OpenldapProvisioning','/var/log/seagate/utils/openldap',level='DEBUG')
    def readinputhostfile(host_file_path):
        global hostlist
        hostlist=[]
        file = open(host_file_path, 'r')
        Lines = file.readlines()
        for line in Lines :
            hostlist.append(line.strip())
        hostlist.sort()

    def checkhostvalidity():
        totalhosts = 0;
        for host in hostlist :
            totalhosts = totalhosts + 1
            exit_code = os.system("ping -c 1 " + host)
            if(exit_code != 0):
                Log.debug(host + ' is either invalid or not reachable.')
                quit()
        return totalhosts
    
    def getserveridfromhostfile():
        serverid = 1
        for host in hostlist :
            if(host == socket.gethostname()):
                break
            serverid = serverid + 1
        return serverid

    def addattribute(conn, dn, attr_to_add, value):
        mod_attrs = [(ldap.MOD_ADD, attr_to_add, bytes(str(value), 'utf-8'))]
        try:
            conn.modify_s(dn,mod_attrs)
        except:
            Log.error('Exception while adding '+ attr_to_add + ' to dn '+ dn)
            raise Exception('Exception while adding '+ attr_to_add + ' to dn '+ dn)

    def deleteattribute_old(conn, dn, attr_to_delete):
        ldap_result_id = conn.search_s(dn, ldap.SCOPE_BASE, None, [attr_to_delete])
        for result1,result2 in ldap_result_id:
            if(result2):
                for value in result2[attr_to_delete]:
                    if(value):
                        mod_attrs = [( ldap.MOD_DELETE, attr_to_delete,value )]
                        try:
                            conn.modify_s(dn,mod_attrs)
                        except:
                            Log.error('Exception while deleting '+attr_to_delete+ ' from dn '+ dn + ' value '+str(value) )

    def deleteattribute(conn, dn, attr_to_delete):
        mod_attrs = [( ldap.MOD_DELETE, attr_to_delete, None  )]
        try:
            conn.modify_s(dn,mod_attrs)
        except:
            Log.error('Exception while deleting '+attr_to_delete+ ' from dn '+ dn  )

    def setreplication(hostfile, pwd, config_values):
        Replication.readinputhostfile(hostfile)
        totalhostcount = Replication.checkhostvalidity()
        id = Replication.getserveridfromhostfile()
        if id > totalhostcount :
            Log.debug('Current host-'+socket.gethostname()+' is not present in input host file')
            quit()
        conn = ldap.initialize("ldapi://")
        conn.simple_bind_s(config_values.get('bind_base_dn'),"seagate")
        conn.sasl_non_interactive_bind_s('EXTERNAL')
        
        dn=config_values.get('serverid_base_dn')
        Replication.deleteattribute(conn, dn, 'olcserverid')
        Replication.addattribute(conn,dn,'olcserverid',id)
        
        dn="cn=module,cn=config"
        add_record = [
         ('objectClass', [b'olcModuleList']),
         ('cn', [b'module'] ),
         ('olcModulePath', [b'/usr/lib64/openldap'] ),
         ('olcModuleLoad', [b'syncprov.la'])
        ]
        try:
            conn.add_s(dn, add_record)
        except:
            Log.error('Exception while adding syncprov_mod')

        dn="olcOverlay=syncprov,olcDatabase={2}mdb,cn=config"
        add_record = [
         ('objectClass', [b'olcOverlayConfig', b'olcSyncProvConfig']),
         ('olcOverlay', [b'syncprov'] ),
         ('olcSpSessionLog', [b'100'] )
        ]
        try:
            conn.add_s(dn, add_record)
        except:
            Log.error('Exception while adding olcOverlay to data')
            raise Exception('Exception while adding olcOverlay to data')

        dn=config_values.get('sync_repl_base_dn')
        Replication.deleteattribute(conn, dn, 'olcSyncrepl')
        ridnum = 0
        for host in hostlist :
            ridnum = ridnum + 1
            value="rid=00"+str(ridnum)+" provider=ldap://"+host+":389/ bindmethod=simple binddn=\""+config_values.get('bind_base_dn')+"\" credentials="+pwd+" searchbase=\""+config_values.get('base_dn')+"\" scope=sub schemachecking=on type=refreshAndPersist retry=\"30 5 300 3\" interval=00:00:05:00"
            Replication.addattribute(conn,dn,'olcSyncrepl',value)
        Replication.deleteattribute(conn,dn,'olcMirrorMode')
        Replication.addattribute(conn,dn,'olcMirrorMode','TRUE')
        conn.unbind_s()
