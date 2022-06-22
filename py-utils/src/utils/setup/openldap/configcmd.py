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
from  ast import literal_eval
from cortx.utils.log import Log
from cortx.utils.setup.openldap.setupcmd import SetupCmd, OpenldapPROVError
from cortx.utils.setup.openldap.base_configure_ldap import BaseConfig
from cortx.utils.setup.openldap.setupReplication import Replication
from pathlib import Path

class ConfigCmd(SetupCmd):

  """Config Setup Cmd."""
  name = "config"
  utils_tmp_dir = "/var/tmp"
  Log.init('OpenldapProvisioning','/var/log/cortx/utils/openldap',level='DEBUG')

  def __init__(self, config: str):
    """Constructor."""
    try:
      super(ConfigCmd, self).__init__(config)
      Log.debug("Inside config phaze, reading credentials from input file")
      self.update_cluster_id()
      self.update_ldap_credentials()
      self.read_ldap_credentials()
    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}\n')

  def process(self):
    """Main processing function."""
    try:
      self.configure_openldap()
    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}\n')

  def configure_openldap(self):
    """Install and Configure Openldap over Non-SSL."""
    Log.debug("Inside config phaze, starting openldap base configuration")
    # Perform base configuration
    base_dn = self.get_confvalue(self.get_confkey('CONFIG>OPENLDAP_BASE_DN'))
    bind_base_dn = 'cn=admin,' + base_dn
    install_dir = self.get_confvalue(self.get_confkey('CONFIG>OPENLDAP_INSTALL_DIR'))
    data_dir = self.get_confvalue(self.get_confkey('CONFIG>OPENLDAP_DATA_DIR'))
    confvalues = {'base_dn':base_dn , 'bind_base_dn':bind_base_dn, 'install_dir':install_dir, 'data_dir':data_dir}
    BaseConfig.perform_base_config(self.rootdn_passwd.decode("utf-8"),'True',confvalues)
    Log.debug("openldap base configuration completed successfully")
    # set openldap-replication
    Log.debug("Starting openldap replication")
    self.configure_openldap_replication(confvalues)
    Log.debug("Openldap replication configured successfully")


  def configure_openldap_replication(self,confvalues):
    """Configure openldap replication within a storage set."""
    storage_set_count = self.get_confvalue(self.get_confkey(
        'CONFIG>CONFSTORE_STORAGE_SET_COUNT_KEY').replace("cluster-id", self.cluster_id))
    index = 0
    while index < int(storage_set_count):
      server_nodes_list = self.get_confkey(
        'CONFIG>CONFSTORE_STORAGE_SET_SERVER_NODES_KEY').replace("cluster-id", self.cluster_id).replace("storage-set-count", str(index))
      server_nodes_list = self.get_confvalue(server_nodes_list)
      if isinstance(server_nodes_list, str):
        # list is stored as string in the confstore file
        server_nodes_list = literal_eval(server_nodes_list)
      if len(server_nodes_list) > 1:
        sys.stdout.write(f'\nSetting ldap-replication for storage_set:{index}\n\n')
        Path(self.utils_tmp_dir).mkdir(parents=True, exist_ok=True)
        ldap_hosts_list_file = os.path.join(self.utils_tmp_dir, "ldap_hosts_list_file.txt")
        with open(ldap_hosts_list_file, "w") as f:
          for node_machine_id in server_nodes_list:
            host_name = self.get_confvalue(f'server_node>{node_machine_id}>hostname')
            f.write(f'{host_name}\n')
        f.close()
        Replication.setreplication(ldap_hosts_list_file,self.rootdn_passwd.decode("utf-8"),confvalues)
        os.remove(ldap_hosts_list_file)
      index += 1
