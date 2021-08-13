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
import ntpath
from shutil import copyfile
from pathlib import Path
from cortx.utils.log import Log
from setupcmd import SetupCmd, OpenldapPROVError

class PreUpgradeCmd(SetupCmd):

  """Pre Upgrade Setup Cmd."""

  name = "preupgrade"
  Log.init('OpenldapProvisioning','/var/log/seagate/utils/openldap',level='DEBUG')

  def __init__(self):
    """Constructor."""
    try:
      super(PreUpgradeCmd, self).__init__(None)
    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}')

  def process(self):
    """Main processing function."""
    try:
        Log.info("Backup .sample to .old started")
        self.backup_sample_file()
        Log.info("Backup .sample to .old completed")
    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}')

  def backup_sample_file(self):
    """Function to backup .sample config file to .old."""
    sampleconfigfile = os.path.join(self.util_install_path, "cortx/utils/conf", "openldap_config.yaml.sample")

    # make utils temp dir if does not exist
    Path(self.utils_tmp_dir).mkdir(parents=True, exist_ok=True)

    # check file exist
    if os.path.isfile(sampleconfigfile):
      #backup .sample to .old at utils temporary location
      copyfile(sampleconfigfile, os.path.join(self.utils_tmp_dir, ntpath.basename(sampleconfigfile) + ".old"))
      Log.info("sample config file %s backup successfully" % sampleconfigfile)
    else:
        Log.error("sample config file %s does not exist" % sampleconfigfile)
        raise Exception("sample config file %s does not exist" % sampleconfigfile)
