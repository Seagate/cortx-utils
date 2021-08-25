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

import os
import ldap
import glob
from shutil import copyfile
from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from setupReplication import Replication
from ldif import LDIFRecordList

class BaseConfig:
    Log.init('OpenldapProvisioning', '/var/log/cortx/utils/openldap', level='DEBUG')
    def add_attribute(binddn, dn, record, pwd):
        #add_s - init.ldif
        # Open a connection
        ldap_conn = ldap.initialize("ldapi:///")
        # Bind/authenticate with a user with apropriate rights to add objects
        ldap_conn.simple_bind_s(binddn, pwd)
        try:
            ldap_conn.add_s(dn, record)
        except Exception:
            Log.error('Error while adding attribute')
            raise Exception('Error while adding attribute')
        ldap_conn.unbind_s()

    def safe_remove(filename):
        try:
            os.remove(filename)
        except Exception:
            Log.error('Error while deleting ' + filename)

    def cleanup(forceclean):
        # Removing schemas
        filelist = glob.glob('/etc/openldap/slapd.d/cn=config/cn=schema/*ppolicy.ldif')
        for policyfile in filelist:
            BaseConfig.safe_remove(policyfile)
        module_files = ["cn=module{0}.ldif", "cn=module{1}.ldif", "cn=module{2}.ldif"]
        for module_file in module_files:
            module_file = '/etc/openldap/slapd.d/cn=config/'+ str(module_file)
            BaseConfig.safe_remove(module_file)
        mdb_directory = '/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb'
        try:
            files = glob.glob('/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb/*')
            for f in files:
                BaseConfig.safe_remove(f)
        except Exception:
            Log.error('Error while deleting '+ mdb_directory)
        mdbfile = '/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif'
        BaseConfig.safe_remove(mdbfile)
        #Data Cleanup
        if forceclean == 'True' :
            files = glob.glob('/var/lib/ldap/*')
            for f in files:
                BaseConfig.safe_remove(f)
        #Clear the password set in config
        conn = ldap.initialize("ldapi:///")
        conn.sasl_non_interactive_bind_s('EXTERNAL')
        Replication.deleteattribute(conn, "olcDatabase={0}config,cn=config", "olcRootPW")
        conn.unbind_s()

    def modify_attribute(dn, attribute, value):
        # Open a connection
        ldap_conn = ldap.initialize("ldapi:///")
        # Bind/authenticate with a user with apropriate rights to add objects
        ldap_conn.sasl_non_interactive_bind_s('EXTERNAL')
        mod_attrs = [(ldap.MOD_REPLACE, attribute, bytes(str(value), 'utf-8'))]
        try:
            ldap_conn.modify_s(dn, mod_attrs)
        except Exception:
            Log.error('Error while modifying attribute- '+ attribute)
            raise Exception('Error while modifying attribute' + attribute)
        ldap_conn.unbind_s()

    def perform_ldif_operation(filename, binddn, rootpassword):
        parser = LDIFRecordList(open(filename, 'r'))
        parser.parse()
        for dn, entry in parser.all_records:
            add_record = list(entry.items())
            BaseConfig.add_attribute(binddn, dn, add_record, rootpassword)

    def perform_base_config(rootpassword, forcecleanup, config_values):
        forceclean = False
        ROOTDNPASSWORD = None
        ROOTDNPASSWORD = rootpassword
        if ROOTDNPASSWORD == None :
            Log.error('Password not provided for ldap configuration')
            quit()
        if forcecleanup != None :
            forceclean = forcecleanup
        mdb_dir = Conf.get(index= 'util_config_file_index', key='install_path') + '/cortx/utils/conf'
        BaseConfig.cleanup(forceclean)
        copyfile(mdb_dir + '/olcDatabase={2}mdb.ldif' ,\
        '/etc/openldap/slapd.d/cn=config/olcDatabase={2}mdb.ldif')
        os.system('chgrp ldap /etc/openldap/certs/password')
        cmd = 'slappasswd -s ' + str(ROOTDNPASSWORD)
        pwd = os.popen(cmd).read()
        pwd.replace('/','\/')
        #restart slapd post cleanup
        os.system('systemctl restart slapd')
        dn = 'olcDatabase={0}config,cn=config'
        BaseConfig.modify_attribute(dn, 'olcRootDN', 'cn=admin,cn=config')
        BaseConfig.modify_attribute(dn, 'olcRootPW', pwd)
        BaseConfig.modify_attribute(dn, 'olcAccess', '{0}to * by dn.base="gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth" write by self write by * read')
        dn = 'olcDatabase={2}mdb,cn=config'
        BaseConfig.modify_attribute(dn, 'olcSuffix', config_values.get('base_dn'))
        BaseConfig.modify_attribute(dn, 'olcRootDN', config_values.get('bind_base_dn'))
        ldap_conn = ldap.initialize("ldapi:///")
        ldap_conn.sasl_non_interactive_bind_s('EXTERNAL')
        mod_attrs = [( ldap.MOD_ADD, 'olcDbMaxSize', [b'10737418240'] )]
        try:
            ldap_conn.modify_s(dn, mod_attrs)
        except Exception:
            Log.error('Error while modifying olcDbMaxSize attribute for olcDatabase={2}mdb')
            raise Exception('Error while modifying olcDbMaxSize attribute for olcDatabase={2}mdb')
        ldap_conn.unbind_s()
        BaseConfig.modify_attribute(dn, 'olcRootPW', pwd)
        BaseConfig.modify_attribute(dn, 'olcAccess', '{0}to attrs=userPassword by self write by dn.base="'+config_values.get('bind_base_dn')+'" write by anonymous auth by * none')
        BaseConfig.modify_attribute(dn, 'olcAccess', '{1}to * by dn.base="'+config_values.get('bind_base_dn')+'" write by self write by * none')

        #add_s - init.ldif
        add_record = [
         ('dc', [b'seagate'] ),
         ('o', [b'seagate'] ),
         ('description', [b'Root entry for seagate.com.']),
         ('objectClass', [b'top',b'dcObject',b'organization'])
        ]
        BaseConfig.add_attribute(config_values.get('bind_base_dn'), config_values.get('base_dn'), add_record, ROOTDNPASSWORD)

        #add iam constraint
        BaseConfig.perform_ldif_operation('/opt/seagate/cortx/utils/conf/iam-constraints.ldif','cn=admin,cn=config',ROOTDNPASSWORD)
        #add ppolicy schema
        BaseConfig.perform_ldif_operation('/etc/openldap/schema/ppolicy.ldif','cn=admin,cn=config',ROOTDNPASSWORD)
        BaseConfig.perform_ldif_operation('/opt/seagate/cortx/utils/conf/ppolicymodule.ldif','cn=admin,cn=config',ROOTDNPASSWORD)
        BaseConfig.perform_ldif_operation('/opt/seagate/cortx/utils/conf/ppolicyoverlay.ldif','cn=admin,cn=config',ROOTDNPASSWORD)
        BaseConfig.perform_ldif_operation('/opt/seagate/cortx/utils/conf/ppolicy-default.ldif',config_values.get('bind_base_dn'),ROOTDNPASSWORD)

