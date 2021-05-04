#!/usr/bin/env python3
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
import os
import ldap
import glob
import argparse
from shutil import copyfile

parser = argparse.ArgumentParser(description="This is ldap base configuration script")
parser.add_argument("--rootdnpasswd", help="Password for root DN")
parser.add_argument("--defaultpasswd", help="Whether to use default password or not")
parser.add_argument("--forceclean", help="Whether to force clean existing configuration or not")
args = parser.parse_args()
defaultpasswd=False
forceclean=False
ROOTDNPASSWORD=None

ROOTDNPASSWORD = args.rootdnpasswd
if args.defaultpasswd != None :
    defaultpasswd = args.defaultpasswd
if args.forceclean != None :
    forceclean = args.forceclean

INSTALLDIR="/opt/seagate/cortx/s3/install/ldap"
#cleanup
# Removing schemas
userSchemaFile = '/etc/openldap/slapd.d/cn=config/cn=schema/cn={1}s3user.ldif'
try:
    os.remove(userSchemaFile)
except:
    print('Error while deleting '+ userSchemaFile)

fileList = glob.glob('/etc/openldap/slapd.d/cn=config/cn=schema/*ppolicy.ldif')
for policyFile in fileList:
    try:
        os.remove(policyFile)
    except:
        print('Error while deleting '+ policyFile)
module0File = '/etc/openldap/slapd.d/cn=config/cn=module{0}.ldif'
try:
    os.remove(module0File)
except:
    print('Error while deleting '+ module0File)
module1File = '/etc/openldap/slapd.d/cn=config/cn=module{1}.ldif'
try:
    os.remove(module1File)
except:
    print('Error while deleting ' + module1File)
module2File = '/etc/openldap/slapd.d/cn=config/cn=module{2}.ldif'
try:
    os.remove(module2File)
except:
    print('Error while deleting ' + module2File)
mdbDirectory = '/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb'
try:
    files = glob.glob('/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb/*')
    for f in files:
        try:
            os.remove(f)
        except:
            print('Error while deleting '+ f)
except:
    print('Error while deleting '+ mdbDirectory)
mdbFile = '/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif'
try:
    os.remove(mdbFile)
except:
    print('Error while deleting '+mdbFile)
#Data Cleanup
if forceclean == 'True' :
    files = glob.glob('/var/lib/ldap/*')
    for f in files:
        try:
            os.remove(f)
        except:
            print('Error while deleting '+ f)


copyfile(INSTALLDIR+'/olcDatabase={2}mdb.ldif' , '/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif')

os.system('chgrp ldap /etc/openldap/certs/password')

if ROOTDNPASSWORD == None :
    if defaultpasswd == 'True' :
        ROOTDNPASSWORD = 'seagate'
    else :
        ROOTDNPASSWORD = input("Enter password for LDAP RootDN ")

cmd = 'slappasswd -s ' + ROOTDNPASSWORD
pwd = os.popen(cmd).read()
pwd.replace('/','\/')
#restart slapd post cleanup
os.system('systemctl restart slapd')

# Open a connection
l = ldap.initialize("ldapi:///")

# Bind/authenticate with a user with apropriate rights to add objects
l.simple_bind_s("cn=admin,dc=seagate,dc=com",ROOTDNPASSWORD)


l.sasl_non_interactive_bind_s('EXTERNAL')
dn="olcDatabase={0}config,cn=config"
mod_attrs = [( ldap.MOD_REPLACE, 'olcRootDN', [b'cn=admin,cn=config'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcRootDN attribute for olcDatabase={0}config')

mod_attrs = [( ldap.MOD_REPLACE, 'olcRootPW', pwd.encode("utf-8") )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcRootPW attribute for olcDatabase={0}config')

mod_attrs = [( ldap.MOD_REPLACE, 'olcAccess', [b'{0}to * by dn.base="gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth" write by self write by * read'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcAccess attribute for olcDatabase={0}config')

dn="olcDatabase={2}mdb,cn=config"
mod_attrs = [( ldap.MOD_REPLACE, 'olcSuffix', [b'dc=seagate,dc=com'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcSuffix attribute for olcDatabase={2}mdb')

mod_attrs = [( ldap.MOD_REPLACE, 'olcRootDN', [b'cn=admin,dc=seagate,dc=com'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcRootDN attribute for olcDatabase={2}mdb')

mod_attrs = [( ldap.MOD_ADD, 'olcDbMaxSize', [b'10737418240'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcDbMaxSize attribute for olcDatabase={2}mdb')

mod_attrs = [( ldap.MOD_REPLACE, 'olcRootPW', pwd.encode("utf-8") )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcRootPW attribute for olcDatabase={2}mdb')

mod_attrs = [( ldap.MOD_REPLACE, 'olcAccess', [b'{0}to attrs=userPassword by self write by dn.base="cn=admin,dc=seagate,dc=com" write by anonymous auth by * none'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcAccess attribute for attrs=userPassword and dn.base=cn=admin,dc=seagate,dc=com in olcDatabase={2}mdb')

mod_attrs = [( ldap.MOD_ADD, 'olcAccess', [b'{1}to * by dn.base="cn=admin,dc=seagate,dc=com" write by self write by * none'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcAccess attribute for * and dn.base=cn=admin,dc=seagate,dc=com in olcDatabase={2}mdb')

mod_attrs = [( ldap.MOD_REPLACE, 'olcAccess', [b'{0}to attrs=userPassword by self write by dn.base="cn=sgiamadmin,dc=seagate,dc=com" write by anonymous auth by * none'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcAccess attribute for attrs=userPassword and dn.base=cn=sgiamadmin,dc=seagate,dc=com in olcDatabase={2}mdb')

mod_attrs = [( ldap.MOD_ADD, 'olcAccess', [b'{1}to * by dn.base="cn=sgiamadmin,dc=seagate,dc=com" write by self write by * none'] )]
try:
    l.modify_s(dn,mod_attrs)
except:
    print('Error while modifying olcAccess attribute for * and dn.base=cn=sgiamadmin,dc=seagate,dc=com in olcDatabase={2}mdb')

l.unbind_s()


#add_s - init.ldif
# Open a connection
l = ldap.initialize("ldapi:///")

# Bind/authenticate with a user with apropriate rights to add objects
l.simple_bind_s("cn=admin,dc=seagate,dc=com",ROOTDNPASSWORD)

dn="dc=seagate,dc=com"
add_record = [
 ('dc', [b'seagate'] ),
 ('o', [b'seagate'] ),
 ('description', [b'Root entry for seagate.com.']),
 ('objectClass', [b'top',b'dcObject',b'organization'])
]
try:
    l.add_s(dn, add_record)
except:
    print('Error while adding dc=seagate,dc=com')

l.unbind_s()
