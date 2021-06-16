import sys
import os
import ldap
import ldap.modlist as modlist
import shutil
import glob
from shutil import copyfile
import socket

class Replication:

    def checkHostValidity(hostFilePath):
        file=open(hostFilePath, 'r')
        Lines=file.readlines()
        totalHosts = 0;
        for line in Lines :
            totalHosts = totalHosts + 1
            #exit_code = os.system(f"ping {parameter} 1 -w2 {ip} > /dev/null 2>&1")
            exit_code = os.system("ping -c 1 " + line.strip())
            if(exit_code == 0):
                print(line.strip() + ' is valid and reachable.')
            else:
                print(line.strip() + ' is either invalid or not reachable.')
                quit()
        return totalHosts
    
    def getServerIdFromHostFile(hostFilePath):
        file=open(hostFilePath, 'r')
        Lines=file.readlines()
        serverId = 1
        for line in Lines :
            if(line.strip() == socket.gethostname()):
                break
            serverId = serverId + 1
        return serverId

    def setReplication(hosts, pwd):
        totalHostCount = Replication.checkHostValidity(hosts)
        id = Replication.getServerIdFromHostFile(hosts)
        if id > totalHostCount :
            print('Current host entry is not present in input host file')
            quit()
        # Open a connection
        l = ldap.initialize("ldapi://")
        # Bind/authenticate with a user with apropriate rights to add objects
        l.simple_bind_s("cn=admin,dc=seagate,dc=com","seagate")
        # The dn of our new entry/object
        l.sasl_non_interactive_bind_s('EXTERNAL')
        dn="cn=config"
        #cleanup serverId
        mod_attrs = [( ldap.MOD_DELETE, 'olcServerID', bytes(str(id), 'utf-8')  )]
        try:
            l.modify_s(dn,mod_attrs)
        except:
            print('Exception while deleting serverId')

        mod_attrs = [( ldap.MOD_ADD, 'olcServerID', bytes(str(id), 'utf-8')  )]
        try:
            l.modify_s(dn,mod_attrs)
        except:
            print('Exception while adding serverId to config')
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
        ridnum = 0
        file=open(hosts, 'r')
        Lines=file.readlines()
        for line in Lines :
            ridnum = ridnum + 1
            value="rid=00"+str(ridnum)+" provider=ldap://"+line.strip()+":389/ bindmethod=simple binddn=cn=admin,cn=config credentials="+pwd+" searchbase=cn=config scope=sub schemachecking=on type=refreshAndPersist retry=30 5 300 3 interval=00:00:05:00"
            mod_attrs = [ ( ldap.MOD_DELETE, 'olcSyncRepl', bytes(value, 'utf-8') )]
            try:
                l.modify_s(dn,mod_attrs)
            except:
                print('Exception while deleting olcSyncRepl from config')
            mod_attrs = [ ( ldap.MOD_ADD, 'olcSyncRepl', bytes(value, 'utf-8') )]
            try:
                l.modify_s(dn,mod_attrs)
            except:
                print('Exception while adding olcSyncRepl to config')
        #cleanup Mirror Mode
        mod_attrs = [( ldap.MOD_DELETE, 'olcMirrorMode', [b'TRUE'])]
        try:
            l.modify_s(dn,mod_attrs)
        except :
            print('Exception while deleting olcMirrorMode from config')

        mod_attrs = [( ldap.MOD_ADD, 'olcMirrorMode', [b'TRUE'])]
        try:
            l.modify_s(dn,mod_attrs)
        except:
            print('Exception while adding olcMirrorMode to config')
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
        for line in Lines :
            ridnum = ridnum + 1
            value="rid=00"+str(ridnum)+" provider=ldap://"+line.strip()+":389/ bindmethod=simple binddn=cn=admin,dc=seagate,dc=com credentials="+pwd+" searchbase=dc=seagate,dc=com scope=sub schemachecking=on type=refreshAndPersist retry=30 5 300 3 interval=00:00:05:00"
            mod_attrs = [ ( ldap.MOD_DELETE, 'olcSyncRepl', bytes(value, 'utf-8') )]
            try:
                l.modify_s(dn,mod_attrs)
            except:
                print('Exception while deleting olcSyncRepl from data')

            mod_attrs = [ ( ldap.MOD_ADD, 'olcSyncRepl', bytes(value, 'utf-8') )]
            try:
                l.modify_s(dn,mod_attrs)
            except:
                print('Exception while adding olcSyncRepl to data')
        #cleanup Mirror Mode
        mod_attrs = [( ldap.MOD_DELETE, 'olcMirrorMode', [b'TRUE'])]
        try:
            l.modify_s(dn,mod_attrs)
        except:
            print('Exception while deleting mirrorMode from data')
        
        mod_attrs = [( ldap.MOD_ADD, 'olcMirrorMode', [b'TRUE'])]
        try:
            l.modify_s(dn,mod_attrs)
        except:
            print('Exception while adding olcMirrorMode to data')


