#!/bin/env python3

# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.

import os
import re
import traceback
from  ast import literal_eval
from cortx.utils.errors import BaseError 
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.validator.v_service import ServiceV
from cortx.utils.validator.v_path import PathV
from cortx.utils.conf_store import Conf
from cortx.utils.log import Log
from configcmd import ConfigCmd
from test import Test
from resetcmd import ResetCmd
from cleanupcmd import CleanupCmd
from preupgradecmd import PreUpgradeCmd
from postupgradecmd import PostUpgradeCmd

class OpenldapSetupError(BaseError):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Set error codes appropriately."""
        if self._rc == 0: return self._desc
        return "error(%d): %s\n\n%s" %(self._rc, self._desc,
            traceback.format_exc())

class Openldap:
    """ Represents Openldap and Performs setup related actions."""
    index = "openldap"
    prov = "provisioning"
    _preqs_conf_file = "/opt/seagate/cortx/utils/conf/openldapsetup_prereqs.json"
    _prov_conf_file = "/opt/seagate/cortx/utils/conf/openldap_prov_config.yaml"
    Log.init('OpenldapProvisioning','/var/log/seagate/utils/openldap',level='DEBUG')
    url = None
    machine_id = None
    cluster_id = None
    cluster_id_key = None

    def __init__(self, conf_url):
        Conf.load(self.prov, f'yaml://{self._prov_conf_file}')
        if not os.path.isfile(self._preqs_conf_file):
            raise Exception("%s file file not found" % (self._preqs_conf_file))
        if conf_url is None:
            Log.debug("Config file is None")
            return
        Conf.load(self.index, f'yaml://{conf_url}')
        self.url = conf_url
        self.machine_id = Conf.machine_id

        self.cluster_id_key = Conf.get(self.prov, \
            'CONFIG>CONFSTORE_CLUSTER_ID_KEY').\
            replace("machine-id", self.machine_id)
        self.cluster_id = Conf.get(self.index, self.cluster_id_key)

    def validate(self, phase: str):
        """ Perform validations for phase."""
        try:
            Conf.load(phase, f'json://{self._preqs_conf_file}')
            prereqs_block = Conf.get(phase, f'{phase}')
            if prereqs_block:
                pip3s = Conf.get(phase, f'{phase}>pip3s')
                if pip3s:
                    PkgV().validate('pip3s', pip3s)
                rpms = Conf.get(phase, f'{phase}>rpms')
                if rpms:
                    PkgV().validate('rpms', rpms)
                services = Conf.get(phase, f'{phase}>services')
                if services:
                    ServiceV().validate('isrunning', services)
                files = Conf.get(phase, f'{phase}>files')
                if files:
                    PathV().validate('exists', files)
            Log.debug("%s - pre-requisite validation complete" % phase)
        except:
            Log.debug("%s - pre-requisite validation failed" % phase)
            raise Exception("prereqs validation failed")
        return 0

    def _key_value_verify(self, key: str, phase: str):
        """Verify if there exists a corresponding value for given key."""
        value = Conf.get(self.index, key)
        if not value:
            Log.debug("Validation failed for %s in %s phase" % (key ,phase))
            raise Exception("Validation failed for %s in %s phase" % (key ,phase))
        else:
            if ((Conf.get(self.prov, 'CONFIG>OPENLDAP_BASE_DN') == key) and (not bool(re.match("^dc=[a-zA-Z0-9]+(,dc=[a-zA-Z0-9]+)+[a-zA-Z0-9]$", value)))):
                Log.debug("Validation failed for %s in %s phase" % (key ,phase))
                raise Exception("Validation failed for %s in %s phase" % (key ,phase))
            if ((Conf.get(self.prov, 'CONFIG>OPENLDAP_BIND_BASE_DN') == key) and (not bool(re.match("^cn=[a-zA-Z0-9]+(,dc=[a-zA-Z0-9]+)+[a-zA-Z0-9]$", value)))):
                Log.debug("Validation failed for %s in %s phase" % (key ,phase))
                raise Exception("Validation failed for %s in %s phase" % (key ,phase))
            if (key.endswith("server_nodes")):
                if type(value) is str:
                    value = literal_eval(value)
                for node_machine_id in value:
                    host_name = Conf.get(self.index, f'server_node>{node_machine_id}>hostname')
                    try:
                        NetworkV().validate('connectivity',[host_name])
                    except:
                        Log.debug("Validation failed for %s>%s>%s in %s phase" % (key, node_machine_id, host_name, phase))
                        raise Exception("Validation failed for %s>%s>%s in %s phase" % (key, node_machine_id, host_name, phase))

    def _get_list_of_phases_to_validate(self, phase_name: str):
        """Get list of all the phases which follow hierarchy pattern."""
        if phase_name == 'POST_INSTALL':
            return ['POST_INSTALL']
        elif phase_name == 'PREPARE':
            return ['POST_INSTALL', 'PREPARE']
        elif phase_name == 'CONFIG':
            return ['POST_INSTALL', 'PREPARE', 'CONFIG']
        elif phase_name == 'INIT':
            return ['POST_INSTALL', 'PREPARE', 'CONFIG', 'INIT']
        elif phase_name == 'TEST':
            return ['TEST']
        elif phase_name == 'RESET':
            return ['RESET']
        elif phase_name == 'CLEANUP':
            return ['CLEANUP']
        elif phase_name == 'PREUPGRADE':
            return ['PREUPGRADE']
        elif phase_name == 'POSTUPGRADE':
            return ['POSTUPGRADE']
        else:
            return []

    def _expand_keys(self, key: str, phase_name: str):
        """Substitute any occurence of machine-id or other such values."""
        cluster_id_val = None
        machine_id_val = self.machine_id
        if self.cluster_id is not None:
            cluster_id_val = self.cluster_id
        else:
            Log.debug("Validation failed for either cluster_id or machine_id in %s phase" % phase_name)
            raise Exception("Validation failed for either cluster_id or machine_id in %s phase" % phase_name)
        """
        The 'storage_set_count' is read using below hard-coded key which is the
        max array size for storage set.
        """
        storage_set_count_key = "cluster>cluster-id>site>storage_set_count"
        storage_set_count_str = None
        storage_set_count_key = storage_set_count_key.\
            replace("cluster-id", cluster_id_val)
        try:
            storage_set_count_str = Conf.get(self.index, storage_set_count_key)
        except:
            Log.debug("Validation failed for storage_set_count in %s phase" % phase_name)
            raise Exception("Validation failed for storage_set_count in %s phase" % phase_name)

        if (storage_set_count_str is not None):
            try:
                storage_set_val = int(storage_set_count_str) - 1
            except ValueError:
                Log.debug("Validation failed for %s in %s phase" % (storage_set_count_key , phase_name))
                raise Exception("Validation failed for %s in %s phase" % (storage_set_count_key , phase_name))
        else:
            storage_set_val = 0

        if key.find("machine-id") != -1:
            key = key.replace("machine-id", str(machine_id_val))
        if key.find("cluster-id") != -1:
            key = key.replace("cluster-id", str(cluster_id_val))
        if key.find("storage-set-count") != -1:
            key = key.replace("storage-set-count", str(storage_set_val))

        return key

    def _get_keys_for_phase(self, phase_name: str):
        """Extract keylist to be used as yardstick for validating keys."""
        prov_keys_list = Conf.get_keys(self.prov)
        phase_key_list = []

        for key in prov_keys_list:
            if key.find(phase_name) == 0:
                value = Conf.get(self.prov, key)
                if value is not None:
                    phase_key_list.append(value)
        return phase_key_list

    def _keys_validate(self, phase_name: str):
        """Validate keys of each phase against argument file."""

        phase_name = phase_name.upper()
        try:
            phase_list = self._get_list_of_phases_to_validate(phase_name)
            yardstick_list = []
            yardstick_list_exp = []
            for phase in phase_list:
                phase_key_list = self._get_keys_for_phase(phase)
                yardstick_list.extend(phase_key_list)
            for key in yardstick_list:
                new_key = self._expand_keys(key, phase_name)
                yardstick_list_exp.append(new_key)
            for key in yardstick_list_exp:
                self._key_value_verify(key,phase_name)
            Log.debug("%s - keys validation complete" % phase_name.lower())
        except:
            raise OpenldapSetupError({"message":"ERROR : Validating keys \
                failed"})

    def post_install(self):
        """ Performs post install operations. Raises exception on error """
        phase_name = "post_install"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        Log.debug("%s - Successful" % phase_name)
        return 0

    def prepare(self):
        """ Perform prepare operations. Raises exception on error """
        phase_name = "prepare"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        Log.debug("%s - Successful" % phase_name)
        return 0

    def config(self):
        """ Performs configurations. Raises exception on error """
        phase_name = "config"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        ConfigCmd(self.url).process()
        Log.debug("%s - Successful" % phase_name)
        return 0

    def init(self):
        """ Perform initialization. Raises exception on error """
        phase_name = "init"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        Log.debug("%s - Successful" % phase_name)
        return 0

    def test(self, plan, config: str):
        """ Perform configuration testing. Raises exception on error """
        phase_name = "test"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        Test(config, "seagate")
        Log.debug("%s - Successful" % phase_name)
        return 0

    def reset(self):
        """ Performs Configuration reset. Raises exception on error """
        phase_name = "reset"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name) 
        ResetCmd(self.url).process()
        Log.debug("%s - Successful" % phase_name)
        return 0

    def cleanup(self):
        """ Performs Configuration cleanup. Raises exception on error """
        phase_name = "cleanup"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name) 
        CleanupCmd(self.url).process()
        Log.debug("%s - Successful" % phase_name)
        return 0

    def preupgrade(self):
        """Perform pre upgrade action."""
        phase_name = "preupgrade"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        PreUpgradeCmd().process()
        Log.debug("%s - Successful" % phase_name)
        return 0

    def postupgrade(self):
        """Perform post upgrade action."""
        phase_name = "postupgrade"
        Log.debug("%s - Starting" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        PostUpgradeCmd().process()
        Log.debug("%s - Successful" % phase_name)
        return 0
