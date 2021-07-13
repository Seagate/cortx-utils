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
from cortx.utils.log import Log
from cortx.utils.conf_store import Conf
from setupcmd import SetupCmd, OpenldapPROVError

class Test(SetupCmd):
    def __init__(self, config: str, passwd):
        try:
            super(Test, self).__init__(config)
        except Exception as e:
            raise OpenldapPROVError(f'exception: {e}\n')

        Log.init('test_log','/var/log/seagate/s3/openldap_prv',level='DEBUG')
        self.test_base_dn(passwd)
        self.test_olcsyncrepl(passwd)
        self.test_olcserverId(passwd)

    def test_base_dn(self,pwd):
        baseDN = self.get_confvalue(self.get_confkey('TEST>OPENLDAP_BASE_DN'))
        bind_base_DN = self.get_confvalue(self.get_confkey('TEST>OPENLDAP_BIND_BASE_DN'))
        searchScope = ldap.SCOPE_BASE
        retrieveAttributes = None
        searchFilter = None
        ldap_conn = ldap.initialize("ldapi://")
        ldap_conn.simple_bind_s(bind_base_DN, pwd)
        try:
            ldap_result_id = ldap_conn.search_s(baseDN, searchScope, searchFilter, retrieveAttributes)
        except ldap.LDAPError as e:
            Log.error(repr(e))
            raise e
        ldap_conn.unbind_s()

    def test_olcsyncrepl(self, pwd):
        baseDN = self.get_confvalue(self.get_confkey('TEST>OPENLDAP_SYNCREPL_BASE_DN'))
        bind_base_DN = self.get_confvalue(self.get_confkey('TEST>OPENLDAP_SYNCREPL_BIND_BASE_DN'))
        searchScope = ldap.SCOPE_BASE
        retrieveAttributes = ['olcSyncrepl']
        searchFilter = None
        ldap_conn = ldap.initialize("ldapi://")
        ldap_conn.simple_bind_s(bind_base_DN, pwd)
        try:
            ldap_result_id = ldap_conn.search_s(baseDN, searchScope, searchFilter, retrieveAttributes)
            for i in ldap_result_id[0]:
                if isinstance(i,dict):
                    if "olcSyncrepl" in i:
                        Log.debug("olcSyncrepl is configured")
                    else:
                        raise Exception("olcSyncrepl is not configured.")
        except (ldap.LDAPError, Exception) as e:
            Log.error(repr(e)) 
            raise e
        ldap_conn.unbind_s()

    def test_olcserverId(self, pwd):
        baseDN = self.get_confvalue(self.get_confkey('TEST>OPENLDAP_SERVERID_BASE_DN'))
        bind_base_DN = self.get_confvalue(self.get_confkey('TEST>OPENLDAP_SERVERID_BIND_BASE_DN'))
        searchScope = ldap.SCOPE_BASE
        retrieveAttributes = ['olcServerID']
        searchFilter = None
        ldap_conn = ldap.initialize("ldapi://")
        ldap_conn.simple_bind_s(bind_base_DN, pwd)
        try:
            ldap_result_id = ldap_conn.search_s(baseDN, searchScope, searchFilter, retrieveAttributes)
            for i in ldap_result_id[0]:
                if isinstance(i,dict):
                    if "olcServerID" in i:
                        Log.debug("olcServerId is configured")
                    else:
                        raise Exception("olcServerId is not configured.")
        except (ldap.LDAPError, Exception) as e:
            Log.error(repr(e))
            raise e
        ldap_conn.unbind_s()
