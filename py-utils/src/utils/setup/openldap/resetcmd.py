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
from cortx.utils.log import Log
from .setupcmd import SetupCmd, OpenldapPROVError

class ResetCmd(SetupCmd):

    """Reset cmd initialization"""
    Log.init('OpenldapProvisioning','/var/log/cortx/utils/openldap',\
             level='DEBUG')
    def __init__(self, config: str):
        """Constructor."""
        try:
            super(ResetCmd, self).__init__(config)
        except Exception as e:
            Log.debug("Initializing reset phase failed")
            raise OpenldapPROVError(f'exception: {e}')

    def process(self):
        """Main processing function."""
        try:
            self.delete_log_files()
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
        Log.debug("Reset completed, empty log file")
