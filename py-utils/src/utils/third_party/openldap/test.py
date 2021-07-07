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


class test(object):
    def __init__(self, passwd):
        Log.init('test_log','/var/log/seagate/s3/openldap_prv',level='DEBUG')
        self.test_base_dn(passwd)
        self.test_olcsyncrepl(passwd)
        self.test_olcserverId(passwd)

    def test_base_dn(self,pwd):
        baseDN = "dc=seagate,dc=com"
        searchScope = ldap.SCOPE_BASE
        retrieveAttributes = None
        searchFilter = None
        ldap_conn = ldap.initialize("ldapi://")
        ldap_conn.simple_bind_s("cn=admin,dc=seagate,dc=com",pwd)
        try:
            ldap_result_id = ldap_conn.search_s(baseDN, searchScope, searchFilter, retrieveAttributes)
        except ldap.LDAPError as e:
            Log.error(repr(e))
            raise e
        ldap_conn.unbind_s()

    def test_olcsyncrepl(self, pwd):
        baseDN = "olcDatabase={2}mdb,cn=config"
        searchScope = ldap.SCOPE_BASE
        retrieveAttributes = ['olcSyncrepl']
        searchFilter = None
        ldap_conn = ldap.initialize("ldapi://")
        ldap_conn.simple_bind_s("cn=admin,cn=config", pwd)
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
        baseDN = "cn=config"
        searchScope = ldap.SCOPE_BASE
        retrieveAttributes = ['olcServerID']
        searchFilter = None
        ldap_conn = ldap.initialize("ldapi://")
        ldap_conn.simple_bind_s("cn=admin,cn=config", pwd)
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
