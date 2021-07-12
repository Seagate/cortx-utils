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
import errno
import shutil
from  ast import literal_eval

from setupcmd import SetupCmd, OpenldapPROVError
from cortx.utils.process import SimpleProcess
from base_configure_ldap import BaseConfig

class ConfigCmd(SetupCmd):
  """Config Setup Cmd."""
  name = "config"

  def __init__(self, config: str):
    """Constructor."""
    try:
      super(ConfigCmd, self).__init__(config)

      self.read_ldap_credentials()

    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}\n')

  def process(self):
    """Main processing function."""
    #sys.stdout.write(f"Processing {self.name} {self.url}\n")
    #self.phase_prereqs_validate(self.name)
    #self.phase_keys_validate(self.url, self.name)

    try:
      self.configure_openldap()
    except Exception as e:
      raise OpenldapPROVError(f'exception: {e}\n')


  def configure_openldap(self):
    """Install and Configure Openldap over Non-SSL."""
    # 1. Install and Configure Openldap over Non-SSL.
    # 2. Enable slapd logging in rsyslog config
    # 3. Set openldap-replication
    # 4. Check number of nodes in the cluster
    # Perform base configuration
    #Put below inside a class  and method and then import it and call
    #os.system('python3 ./../../third_party/openldap/base_configure_ldap.py --forceclean True --rootdnpasswd ' + self.rootdn_passwd)
    BaseConfig.performbaseconfig(self.rootdn_passwd,'True')
    if os.path.isfile("/opt/seagate/cortx/s3/install/ldap/rsyslog.d/slapdlog.conf"):
      try:
        os.makedirs("/etc/rsyslog.d")
      except OSError as e:
        if e.errno != errno.EEXIST:
          raise OpenldapPROVError(f"mkdir /etc/rsyslog.d failed with errno: {e.errno}, exception: {e}\n")
      shutil.copy('/opt/seagate/cortx/s3/install/ldap/rsyslog.d/slapdlog.conf',
                  '/etc/rsyslog.d/slapdlog.conf')

    # restart rsyslog service
    try:
      sys.stdout.write("Restarting rsyslog service...\n")
      service_list = ["rsyslog"]
      self.restart_services(service_list)
    except Exception as e:
      sys.stderr.write(f'Failed to restart rsyslog service, error: {e}\n')
      raise e
    sys.stdout.write("Restarted rsyslog service...\n")

    # set openldap-replication
    self.configure_openldap_replication()
    
    sys.stdout.write("INFO: Successfully configured openldap on the node.\n")

  def configure_openldap_replication(self):
    """Configure openldap replication within a storage set."""
    storage_set_count = self.get_confvalue(self.get_confkey(
        'CONFIG>CONFSTORE_STORAGE_SET_COUNT_KEY').replace("cluster-id", self.cluster_id))

    index = 0
    while index < int(storage_set_count):
      server_nodes_list = self.get_confkey(
        'CONFIG>CONFSTORE_STORAGE_SET_SERVER_NODES_KEY').replace("cluster-id", self.cluster_id).replace("storage-set-count", str(index))
      server_nodes_list = self.get_confvalue(server_nodes_list)
      if type(server_nodes_list) is str:
        # list is stored as string in the confstore file
        server_nodes_list = literal_eval(server_nodes_list)

      if len(server_nodes_list) > 1:
        sys.stdout.write(f'\nSetting ldap-replication for storage_set:{index}\n\n')

        with open("hosts_list_file.txt", "w") as f:
          for node_machine_id in server_nodes_list:
            hostname = self.get_confvalue(f'server_node>{node_machine_id}>hostname')
            f.write(f'{hostname}\n')
        #TODO make python call below
        #cmd = ['/opt/seagate/cortx/s3/install/ldap/replication/setupReplicationScript.sh',
        #     '-h',
        #     'hosts_list_file.txt',
        #     '-p',
        #     f'{self.rootdn_passwd}']
        #handler = SimpleProcess(cmd)
        #stdout, stderr, retcode = handler.run()

        #os.remove("hosts_list_file.txt")

        #if retcode != 0:
        #  raise OpenldapPROVError(f"{cmd} failed with err: {stderr}, out: {stdout}, ret: {retcode}\n")
      index += 1

