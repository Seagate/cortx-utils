import sys
import os
import ldap
import ldap.modlist as modlist
import shutil
import glob
from shutil import copyfile
import socket

class Replication:
hostList = []
    def readInputHostFile(hostFilePath):
        file=open(hostFilePath, 'r')
        Lines=file.readlines()
        for line in Lines :
            hostList.append(line.strip())

    def checkHostValidity():
        totalHosts = 0;
        for host in hostList :
            totalHosts = totalHosts + 1
            exit_code = os.system("ping -c 1 " + host)
            if(exit_code == 0):
                print(host + ' is valid and reachable.')
            else:
                print(host + ' is either invalid or not reachable.')
                quit()
        return totalHosts
    
    def getServerIdFromHostFile():
        serverId = 1
        for host in hostList :
            if(host == socket.gethostname()):
                break
            serverId = serverId + 1
        return serverId

    def addAttribute(l, dn, attrToAdd, value):
        mod_attrs = [( ldap.MOD_ADD, attrToAdd, bytes(str(value), 'utf-8')  )]
        try:
            l.modify_s(dn,mod_attrs)
        except:
            print('Exception while adding '+ attrToAdd + 'to dn '+ dn)

    def deleteAttribute(l, dn, attrToDelete):
        ldap_result_id = l.search_s(dn, ldap.SCOPE_BASE, None, [attrToDelete])
        for result1,result2 in ldap_result_id:
        if(result2):
        for value in result2[attrToDelete]:
            if(value):
                mod_attrs = [( ldap.MOD_DELETE, attrToDelete, value  )]
                try:
                    l.modify_s(dn,mod_attrs)
                except:
                    print('Exception while deleting '+attrToDelete)

    def setReplication(hosts, pwd):
        Replication.readInputHostFile(hostFile)
        totalHostCount = Replication.checkHostValidity()
        id = Replication.getServerIdFromHostFile()
        if id > totalHostCount :
            print('Current host entry is not present in input host file')
            quit()
        l = ldap.initialize("ldapi://")
        l.simple_bind_s("cn=admin,dc=seagate,dc=com","seagate")
        l.sasl_non_interactive_bind_s('EXTERNAL')
        
        dn="cn=config"
        Replication.deleteAttribute(l, dn, 'olcServerID')
        Replication.addAttribute(l,dn,'olcServerID',id)
        
        dn="cn=module,cn=config"
        add_record = [
         ('objectClass', [b'olcModuleList']),
         ('cn', [b'module'] ),
         ('olcModulePath', [b'/usr/lib64/openldap'] ),
         ('olcModuleLoad', [b'syncprov.la'])
        ]
        try:
            l.add_s(dn, add_record)
        except:
            print('Exception while adding syncprov_mod')
        dn="olcOverlay=syncprov,olcDatabase={0}config,cn=config"
        add_record = [
         ('objectClass', [b'olcOverlayConfig', b'olcSyncProvConfig']),
         ('olcOverlay', [b'syncprov'] ),
         ('olcSpSessionLog', [b'100'] )
        ]
        try:
            l.add_s(dn, add_record)
        except:
            print('Exception while adding olcOverlay to config')

        dn="olcDatabase={0}config,cn=config"
        Replication.deleteAttribute(l, dn, 'olcSyncrepl')
        ridnum = 0
        for host in hostList :
            ridnum = ridnum + 1
            value="rid=00"+str(ridnum)+" provider=ldap://"+host+":389/ bindmethod=simple binddn=cn=admin,cn=config credentials="+pwd+" searchbase=cn=config scope=sub schemachecking=on type=refreshAndPersist retry=30 5 300 3 interval=00:00:05:00"
            Replication.addAttribute(l,dn,'olcSyncRepl',value)
        
        Replication.deleteAttribute(l,dn,'olcMirrorMode')
        Replication.addAttribute(l,dn,'olcMirrorMode','TRUE')
        
        dn="olcOverlay=syncprov,olcDatabase={2}mdb,cn=config"
        add_record = [
         ('objectClass', [b'olcOverlayConfig', b'olcSyncProvConfig']),
         ('olcOverlay', [b'syncprov'] ),
         ('olcSpSessionLog', [b'100'] )
        ]
        try:
            l.add_s(dn, add_record)
        except:
            print('Exception while adding olcOverlay to data')

        dn="olcDatabase={2}mdb,cn=config"
        Replication.deleteAttribute(l, dn, 'olcSyncrepl')
        for host in hostList :
            ridnum = ridnum + 1
            value="rid=00"+str(ridnum)+" provider=ldap://"+host+":389/ bindmethod=simple binddn=cn=admin,dc=seagate,dc=com credentials="+pwd+" searchbase=dc=seagate,dc=com scope=sub schemachecking=on type=refreshAndPersist retry=30 5 300 3 interval=00:00:05:00"
            Replication.addAttribute(l,dn,'olcSyncRepl',value)

        Replication.deleteAttribute(l,dn,'olcMirrorMode')
        Replication.addAttribute(l,dn,'olcMirrorMode','TRUE')
