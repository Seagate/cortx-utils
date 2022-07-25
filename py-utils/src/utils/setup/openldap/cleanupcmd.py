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
from cortx.utils.setup.openldap.setupcmd import SetupCmd, OpenldapPROVError
from cortx.utils.setup.openldap.base_configure_ldap import BaseConfig
from cortx.utils.setup.openldap.setupReplication import Replication

class CleanupCmd(SetupCmd):
    """Cleanup cmd initialization."""

    Log.init('OpenldapProvisioning','/var/log/cortx/utils/openldap',\
             level='DEBUG')
    def __init__(self, config: str):
        """Constructor."""
        try:
            super(CleanupCmd, self).__init__(config)
        except Exception as e:
            Log.debug("Initializing cleanup phase failed")
            raise OpenldapPROVError(f'exception: {e}')

    def process(self):
        """Main processing function."""
        try:
            self.delete_replication_config()
            self.delete_log_files()
            install_dir = self.get_confvalue(self.get_confkey('CONFIG>OPENLDAP_INSTALL_DIR'))
            data_dir = self.get_confvalue(self.get_confkey('CONFIG>OPENLDAP_DATA_DIR'))
            BaseConfig.cleanup(True, install_dir, data_dir)
            # restart slapd
            if(os.system('kill -15 $(pidof slapd)')!=0) :
                Log.error('failed to kill slapd process while cleanup')
                quit()
            if(os.system('/usr/sbin/slapd -F '+install_dir +'/openldap/slapd.d -u ldap -h \'ldapi:/// ldap:///\'')!=0) :
                Log.error('failed to start slapd in cleanup')
                quit()

        except Exception as e:
            raise OpenldapPROVError(f'exception: {e}\n')

    def _delete_file(self, filepath: str):
        """Delete file."""
        if os.path.exists(filepath):
            try:
                file_shrink = open(filepath, "w")
                file_shrink.truncate()
                file_shrink.close()
            except Exception:
                Log.debug("Failed deleting log file : %s" % filepath)

    def delete_log_files(self):
        """Delete log files."""
        Log.debug("Starting log file deletion")
        logFiles = ["/var/log/cortx/utils/openldap/OpenldapProvisioning.log",
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

        dn = "olcDatabase={2}mdb,cn=config"
        Replication.deleteattribute(conn, dn, "olcSyncrepl")
        Replication.deleteattribute(conn, dn, "olcMirrorMode")
