#!/usr/bin/env python3
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
import re
import shutil
from os import path
from cortx.utils.security.cipher import Cipher
from cortx.utils.conf_store import Conf
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.validator.v_service import ServiceV
from cortx.utils.validator.v_path import PathV
from cortx.utils.process import SimpleProcess
from cortx.utils.log import Log

class OpenldapPROVError(Exception):
  """Parent class for the openldap provisioner error classes."""
  pass

class SetupCmd(object):
  """Base class for setup commands."""
  ldap_user = None
  ldap_passwd = None
  ldap_root_user = None
  rootdn_passwd = None
  cluster_id = None
  machine_id = None
  ldap_mdb_folder = "/var/lib/ldap"
  openldap_prov_config = "/opt/seagate/cortx/utils/conf/openldap_prov_config.yaml"
  _preqs_conf_file = "openldapsetup_prereqs.json"
  ha_service_map = {}
  openldap_config_file = "/opt/seagate/cortx/utils/conf/openldap_config.yaml"
  sgiam_user_key = 'cluster_config>sgiam_user'
  sgiam_pass_key = 'cluster_config>sgiam_password'
  rootdn_user_key = 'cluster_config>rootdn_user'
  rootdn_pass_key = 'cluster_config>rootdn_password'
  cluster_id_key = 'cluster_config>cluster_id'
  Log.init('OpenldapProvisioning','/var/log/seagate/utils/openldap',level='DEBUG')

  def __init__(self, config: str):
    """Constructor."""
    if config is None:
      return

    if not config.strip():
      sys.stderr.write(f'config url:[{config}] must be a valid url path\n')
      raise Exception('empty config URL path')

    self.endpoint = None
    self._url = config
    Conf.load('prov_index', self._url)
    Conf.load('openldap_keys_index', f'yaml://{self.openldap_prov_config}')

    # machine_id will be used to read confstore keys
    with open('/etc/machine-id') as f:
      self.machine_id = f.read().strip()

    self.cluster_id = self.get_confvalue(self.get_confkey('CONFIG>CONFSTORE_CLUSTER_ID_KEY').replace("machine-id", self.machine_id))

  @property
  def url(self) -> str:
    return self._url

  def get_confkey(self, key: str):
    return Conf.get('openldap_keys_index',key)

  def get_confvalue(self, key: str):
    return Conf.get('prov_index',key)

  def read_endpoint_value(self):
    if self.endpoint is None:
      self.endpoint = self.get_confvalue(self.get_confkey('TEST>CONFSTORE_ENDPOINT_KEY'))

  def read_ldap_credentials(self):
    """Read ldap credentials (rootdn, sgiam) from the openldap_config file"""
    try:
      # Load the openldap config file
      index_id = 'openldap_config_file_read_index'
      Conf.load(index_id, f'yaml://{self.openldap_config_file}')

      # Read the cluster id from openldap_config file
      self.cluster_id = Conf.get(index_id, f'{self.cluster_id_key}')

      cipher_key = Cipher.generate_key(self.cluster_id , self.get_confkey('CONFSTORE_OPENLDAP_CONST_KEY'))

      # sgiam username/password
      self.ldap_user = Conf.get(index_id, f'{self.sgiam_user_key}')

      encrypted_ldapadmin_pass = Conf.get(index_id, f'{self.sgiam_pass_key}')
      if encrypted_ldapadmin_pass != None:
        self.ldap_passwd = Cipher.decrypt(cipher_key, bytes(str(encrypted_ldapadmin_pass), 'utf-8'))

      # rootdn username/password
      self.ldap_root_user = Conf.get(index_id, f'{self.rootdn_user_key}')
      encrypted_rootdn_pass = Conf.get(index_id, f'{self.rootdn_pass_key}')
      if encrypted_rootdn_pass != None:
        self.rootdn_passwd = Cipher.decrypt(cipher_key, bytes(str(encrypted_rootdn_pass),'utf-8'))

    except Exception as e:
      Log.error(f'read ldap credentials failed, error: {e}')
      raise e

  def update_cluster_id(self):
    """Update 'cluster_id' to openldap_config file."""
    try:
      if path.isfile(f'{self.openldap_config_file}') == False:
        raise Exception(f'{self.openldap_config_file} must be present')
      else:
        key = 'cluster_config>cluster_id'
        index_id = 'openldap_config_file_cluster_id_index'
        Conf.load(index_id, f'yaml://{self.openldap_config_file}')
        Conf.set(index_id, f'{key}', f'{self.cluster_id}')
        Conf.save(index_id)
        updated_cluster_id = Conf.get(index_id, f'{key}')

        if updated_cluster_id != self.cluster_id:
          Log.error(f'failed to set {key}: {self.cluster_id} in {self.openldap_config_file} ')
          raise Exception(f'failed to set {key}: {self.cluster_id} in {self.openldap_config_file} ')
    except Exception as e:
      Log.error(f'Update cluster id failed, error: {e}')
      raise Exception(f'exception: {e}')

  def update_ldap_credentials(self):
    """Update ldap credentials (rootdn, sgiam) to openldap_config file."""
    try:
      # Load the openldap config file
      index_id = 'openldap_config_file_write_index'
      Conf.load(index_id, f'yaml://{self.openldap_config_file}')

      # get the sgiam credentials from provisoner config file
      # set the sgiam credentials in to openldap_config file
      ldap_user = self.get_confvalue(self.get_confkey('CONFIG>CONFSTORE_LDAPADMIN_USER_KEY'))
      encrypted_ldapadmin_pass = self.get_confvalue(self.get_confkey('CONFIG>CONFSTORE_LDAPADMIN_PASSWD_KEY'))
      if encrypted_ldapadmin_pass is None:
        Log.error('sgiam password cannot be None.')
        raise Exception('sgiam password cannot be None.')
      Conf.set(index_id, f'{self.sgiam_user_key}', f'{ldap_user}')
      Conf.set(index_id, f'{self.sgiam_pass_key}', f'{encrypted_ldapadmin_pass}')

      # get the rootdn credentials from provisoner config file
      # set the rootdn credentials in to openldap_config file
      ldap_root_user = self.get_confvalue(self.get_confkey('CONFIG>CONFSTORE_ROOTDN_USER_KEY'))
      encrypted_rootdn_pass = self.get_confvalue(self.get_confkey('CONFIG>CONFSTORE_ROOTDN_PASSWD_KEY'))
      if encrypted_rootdn_pass is None:
        Log.error('rootdn password cannot be None.')
        raise Exception('rootdn password cannot be None.')
      Conf.set(index_id, f'{self.rootdn_user_key}', f'{ldap_root_user}')
      Conf.set(index_id, f'{self.rootdn_pass_key}', f'{encrypted_rootdn_pass}')

      # save openldap config file
      Conf.save(index_id)

    except Exception as e:
      Log.error(f'update rootdn credentials failed, error: {e}')
      raise Exception(f'update rootdn credentials failed, error: {e}')

  def restart_services(self, s3services_list):
    """Restart services specified as parameter."""
    for service_name in s3services_list:
      try:
        # if service name not found in the ha_service_map then use systemctl
        service_name = self.ha_service_map[service_name]
        cmd = ['cortx', 'restart',  f'{service_name}']
      except KeyError:
        cmd = ['/bin/systemctl', 'restart',  f'{service_name}']
      handler = SimpleProcess(cmd)
      res_op, res_err, res_rc = handler.run()
      if res_rc != 0:
        raise Exception(f"{cmd} failed with err: {res_err}, out: {res_op}, ret: {res_rc}")


  def validate_pre_requisites(self,
                        rpms: list = None,
                        pip3s: list = None,
                        services: list = None,
                        files: list = None):
    """Validate pre requisites using cortx-py-utils validator."""
    sys.stdout.write(f'Validations running from {self._preqs_conf_file}\n')
    if pip3s:
      PkgV().validate('pip3s', pip3s)
    if services:
      ServiceV().validate('isrunning', services)
    if rpms:
      PkgV().validate('rpms', rpms)
    if files:
      PathV().validate('exists', files)

  def phase_prereqs_validate(self, phase_name: str):
    """Validate pre requisites using cortx-py-utils validator for the 'phase_name'."""
    if not os.path.isfile(self._preqs_conf_file):
      raise FileNotFoundError(f'pre-requisite json file: {self._preqs_conf_file} not found')
    Conf.load('preqsConfFileIndex', f'json://{self._preqs_conf_file}')
    try:
      prereqs_block = Conf.get('preqsConfFileIndex',f'{phase_name}')
      if prereqs_block is not None:
        self.validate_pre_requisites(rpms=Conf.get('preqsConfFileIndex',f'{phase_name}>rpms'),
                                services=Conf.get('preqsConfFileIndex',f'{phase_name}>services'),
                                pip3s=Conf.get('preqsConfFileIndex',f'{phase_name}>pip3s'),
                                files=Conf.get('preqsConfFileIndex',f'{phase_name}>files'))
    except Exception as e:
      raise OpenldapPROVError(f'ERROR: {phase_name} prereqs validations failed, exception: {e} \n')

  def extract_yardstick_list(self, phase_name: str):
    """Extract keylist to be used as yardstick for validating keys of each phase."""
    # The openldap prov config file has below pairs :
    # "Key Constant" : "Actual Key"
    # Example of "Key Constant" :
    #   CONFSTORE_SITE_COUNT_KEY
    #   PREPARE
    #   CONFIG>CONFSTORE_LDAPADMIN_USER_KEY
    #   INIT
    # Example of "Actual Key" :
    #   cluster>cluster-id>site>storage_set_count
    #   cortx>software>openldap>sgiam>user
    #
    # When we call get_all_keys on openldap prov config
    # file, it returns all the "Key Constant",
    # which will contain PHASE(name) as the root
    # attribute (except for unsolicited keys).
    # To get "Actual Key" from each "Key Constant",
    # we need to call get_confkey on every such key.
    #
    # Note that for each of these "Key Constant",
    # there may not exist an "Actual Key" because
    # some phases do not have any "Actual Key".
    # Example of such cases -
    #   POST_INSTALL
    #   PREPARE
    # For such examples, we skip and continue with
    # remaining keys.

    prov_keys_list = Conf.get_keys('openldap_keys_index')
    # We have all "Key Constant" in prov_keys_list,
    # now extract "Actual Key" if it exists and
    # depending on phase and hierarchy, decide
    # whether it should be added to the yardstick
    # list for the phase passed here.
    yardstick_list = []
    prev_phase = True
    curr_phase = False
    next_phase = False
    for key in prov_keys_list:
      # If PHASE is not relevant, skip the key.
      # Or set flag as appropriate. For test,
      # reset and cleanup, do not inherit keys
      # from previous phases.
      if next_phase:
        break
      if key.find(phase_name) == 0:
        prev_phase = False
        curr_phase = True
      else:
        if (
             phase_name == "TEST" or
             phase_name == "RESET" or
             phase_name == "CLEANUP"
           ):
            continue
        if not prev_phase:
          curr_phase = False
          next_phase = True
          break
      value = self.get_confkey(key)
      # If value does not exist which can be the
      # case for certain phases as mentioned above,
      # skip the value.
      if value is None:
        continue
      yardstick_list.append(value)
    return yardstick_list

  def phase_keys_validate(self, arg_file: str, phase_name: str):
    # Setting the desired values before we begin
    token_list = ["machine-id", "cluster-id", "storage-set-count"]
    if self.machine_id is not None:
      machine_id_val = self.machine_id
    if self.cluster_id is not None:
      cluster_id_val = self.cluster_id
    # The 'storage_set_count' is read using
    # below hard-coded key which is the max
    # array size for storage set.
    storage_set_count_key = "cluster>cluster-id>site>storage_set_count"
    if self.cluster_id is not None:
      storage_set_count_key = storage_set_count_key.replace("cluster-id", cluster_id_val)
    storage_set_count_str = self.get_confvalue(storage_set_count_key)
    if storage_set_count_str is not None:
      storage_set_val = int(storage_set_count_str)
    else:
      storage_set_val = 0
    # Set phase name to upper case required for inheritance
    phase_name = phase_name.upper()
    try:
      # Extract keys from yardstick file for current phase considering inheritance
      yardstick_list = self.extract_yardstick_list(phase_name)

      # Set argument file confstore
      Conf.load('argument_file_index',arg_file)
      # Extract keys from argument file
      arg_keys_list = Conf.get_keys()
      # Since get_all_keys misses out listing entries inside
      # an array, the below code is required to fetch such
      # array entries. The result will be stored in a full
      # list which will be complete and will be used to verify
      # keys required for each phase.
      full_arg_keys_list = []
      for key in arg_keys_list:
        if ((key.find('[') != -1) and (key.find(']') != -1)):
          storage_set = self.get_confvalue(key)
          base_key = key
          for set_key in storage_set:
            key = base_key + ">" + set_key
            full_arg_keys_list.append(key)
        else:
          full_arg_keys_list.append(key)

      # Below algorithm uses tokenization
      # of both yardstick and argument key
      # based on delimiter to generate
      # smaller key-tokens. Then check if
      # (A) all the key-tokens are pairs of
      #     pre-defined token. e.g.,
      #     if key_yard is machine-id, then
      #     key_arg must have corresponding
      #     value of machine_id_val.
      # OR
      # (B) both the key-tokens from key_arg
      #     and key_yard are the same.
      list_match_found = True
      key_match_found = False
      for key_yard in yardstick_list:
        key_yard_token_list = re.split('>|\[|\]',key_yard)
        key_match_found = False
        for key_arg in full_arg_keys_list:
          if key_match_found is False:
            key_arg_token_list = re.split('>|\[|\]',key_arg)
            if len(key_yard_token_list) == len(key_arg_token_list):
              for key_x,key_y in zip(key_yard_token_list, key_arg_token_list):
                key_match_found = False
                if key_x == "machine-id":
                  if key_y != machine_id_val:
                    break
                elif key_x == "cluster-id":
                  if key_y != cluster_id_val:
                    break
                elif key_x == "storage-set-count":
                  if int(key_y) >= storage_set_val:
                    break
                elif key_x != key_y:
                  break
                key_match_found = True
        if key_match_found is False:
          list_match_found = False
          break
      if list_match_found is False:
        raise Exception(f'No match found for {key_yard}')
      sys.stdout.write("Validation complete\n")

    except Exception as e:
      raise Exception(f'ERROR : Validating keys failed, exception {e}\n')
