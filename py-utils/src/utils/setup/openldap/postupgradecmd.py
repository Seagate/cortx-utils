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
from cortx.utils.conf_store import Conf
from setupcmd import SetupCmd, OpenldapPROVError


class PostUpgradeCmd(SetupCmd):

  """Post Upgrade Setup Cmd."""

  name = "postupgrade"
  Log.init('OpenldapProvisioning','/var/log/cortx/utils/openldap',level='DEBUG')

  def __init__(self):
    """Constructor."""
    try:
      super(PostUpgradeCmd, self).__init__(None)
    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}')

  def process(self):
    """Main processing function."""
    try:
      configFile = os.path.join(self.util_install_path, "cortx/utils/conf", "openldap_config.yaml")
      oldSampleFile = os.path.join(self.utils_tmp_dir, "openldap_config.yaml.sample.old")
      newSampleFile = os.path.join(self.util_install_path, "cortx/utils/conf", "openldap_config.yaml.sample")
      unsafeAttributesFile = os.path.join(self.util_install_path, "cortx/utils/conf", "openldap_config_unsafe_attributes.yaml")
      fileType = 'yaml://'
      # Upgrade config files
      Log.info("merge config started")
      self.merge_config(configFile, oldSampleFile, newSampleFile, unsafeAttributesFile, fileType)
      Log.info("merge config completed")

      # Remove temporary .old files from temporary location
      Log.info("Remove sample.old file started")
      if os.path.isfile(oldSampleFile):
        os.remove(oldSampleFile)
      Log.info("Remove sample.old file completed")

    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}')

  def merge_config(self, configFile:str, oldSampleFile:str, newSampleFile:str, unsafeAttributesFile:str, filetype:str):
    """Core logic for updating config files during upgrade using conf store.
    Following is algorithm from merge:
    Iterate over all parameters sample.new file
    for every parameter, check
    - if it is marked as 'unsafe' in attributes file, skip
    - if it marked as 'safe' in the attributes file
        - diff the value in config and sample.old - if it is changed, skip
        - if it is not changed,  we will overwrite the value in cfg file from sample.new
        - if it does not exist in cfg file add the value from sample.new file to cfg file
    - All the arrays in yaml are always overwritten"""
    #If config file is not present then abort merging.
    if not os.path.isfile(configFile):
        Log.error("config file %s does not exist" % configFile)
        raise Exception("ERROR: config file %s does not exist" % configFile)

    Log.info("config file %s upgrade started." % configFile)

    # old sample file
    conf_old_sample = filetype + oldSampleFile
    conf_old_sample_index = "conf_old_sample_index"
    Conf.load(conf_old_sample_index, conf_old_sample)

    # new sample file
    conf_new_sample = filetype + newSampleFile
    conf_new_sample_index = "conf_new_sample_index"
    Conf.load(conf_new_sample_index, conf_new_sample)
    conf_new_sample_keys = Conf.get_keys(conf_new_sample_index)

    # unsafe attribute file
    conf_unsafe_file = filetype + unsafeAttributesFile
    conf_unsafe_file_index = "conf_unsafe_file_index"
    Conf.load(conf_unsafe_file_index, conf_unsafe_file)
    conf_unsafe_file_keys = Conf.get_keys(conf_unsafe_file_index)

    # active config file
    conf_file =  filetype + configFile
    conf_file_index = "conf_file_index"
    Conf.load(conf_file_index, conf_file)
    conf_file_keys = Conf.get_keys(conf_file_index)

    #logic to determine which keys to merge.
    keys_to_overwrite = []
    for key in conf_new_sample_keys:
        #If key is marked for unsafe then do not modify/overwrite.
        if key in conf_unsafe_file_keys:
            continue
        #if key not present active config file then add it
        if key not in conf_file_keys:
            keys_to_overwrite.append(key)
        #if key is not unsafe and value is not changed by user then overwrite it.
        elif Conf.get(conf_file_index, key) == Conf.get(conf_old_sample_index, key):
            keys_to_overwrite.append(key)
        #if user has changed the value of the key then skip it.
        else:
            continue

    Conf.copy(conf_new_sample_index, conf_file_index, keys_to_overwrite)
    Conf.save(conf_file_index)
    Log.info("config file %s upgrade completed" % configFile)
