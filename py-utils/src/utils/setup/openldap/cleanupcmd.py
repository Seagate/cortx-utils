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

import os
import ldap
from cortx.utils.log import Log
from setupcmd import SetupCmd, OpenldapPROVError
from base_configure_ldap import BaseConfig
from setupReplication import Replication

class CleanupCmd(SetupCmd):
    """Cleanup cmd initialization"""
    Log.init('OpenldapProvisioning','/var/log/seagate/utils/openldap',\
             level='DEBUG')
    def __init__(self):
        """Constructor"""
        try:
            super(CleanupCmd, self).__init__()
        except Exception as e:
            Log.debug("Initializing cleanup phase failed")
            raise OpenldapPROVError(f'exception: {e}')

    def process(self):
        """Main processing function."""
        try:
            self.delete_log_files()
            BaseConfig.cleanup(True)
            os.system('systemctl restart slapd')
            self.delete_replication_config()
        except Exception as e:
            raise OpenldapPROVError(f'exception: {e}\n')

    def _delete_file(self, filepath: str):
        """Delete file."""
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                Log.debug("Failed deleting log file")

    def delete_log_files(self):
        """Delete log files."""
        Log.debug("Starting log file deletion")
        logFiles = ["/var/log/seagate/utils/openldap/OpenldapProvisioning",
                    "/var/log/slapd.log"]
        for logFile in logFiles:
            self._delete_file(logFile)
        Log.debug("Cleanup completed, empty log file")

    def delete_replication_config(self):
        """Cleanup replication related config."""
        Log.debug("Starting replication cleanup")
        conn = ldap.initialize("ldapi://")
        conn.sasl_non_interactive_bind_s('EXTERNAL')

        dn = "cn=config"
        Replication.deleteattribute(conn, dn, "olcServerID")

        dn = "olcDatabase={0}config,cn=config"
        Replication.deleteattribute(conn, dn, "olcSyncrepl")
        Replication.deleteattribute(conn, dn, "olcMirrorMode")

        dn = "olcDatabase={2}mdb,cn=config"
        Replication.deleteattribute(conn, dn, "olcSyncrepl")
        Replication.deleteattribute(conn, dn, "olcMirrorMode")
