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

from cortx.utils.errors import BaseError 
from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.validator.v_service import ServiceV
from cortx.utils.conf_store import Conf
from cortx.utils.log import Log
from test import Test

class OpenldapSetupError(BaseError):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
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
    url = ""

    def __init__(self, conf_url):
        if not os.path.isfile(self._preqs_conf_file):
            raise OpenldapSetupError({"message":"pre-requisite json file \
                not found"})
        Conf.load(self.index, f'yaml://{conf_url}')
        Conf.load(self.prov, f'yaml://{self._prov_conf_file}')
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
            Log.debug("%s - pre-requisite validation complete\n" % phase)
        except OpenldapSetupError as e:
            raise OpenldapSetupError({"message":"prereqs validation failed"})
        return 0

    def _key_value_verify(self, key: str, phase: str):
        """Verify if there exists a corresponding value for given key."""

        value = Conf.get(self.index, key)
        if not value:
            Log.debug("Validation failed for %s in %s phase\n" % (key ,phase))
            raise Exception("Validation failed for %s in %s phase" % (key ,phase))
        else:
            address_token = ["hostname"]
            for token in address_token:
                if key.find(token) != -1:
                    NetworkV().validate('connectivity',[value])
                    break

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
        else:
            return []

    def _expand_keys(self, key: str, phase_name: str):
        """Substitute any occurence of machine-id or other such values."""
        cluster_id_val = None
        machine_id_val = None
        if self.machine_id is not None:
            machine_id_val = self.machine_id
        if self.cluster_id is not None:
            cluster_id_val = self.cluster_id
        """
        The 'storage_set_count' is read using below hard-coded key which is the
        max array size for storage set.
        """
        storage_set_count_key = "cluster>cluster-id>site>storage_set_count"
        storage_set_count_str = None
        if self.cluster_id is not None:
            storage_set_count_key = storage_set_count_key.\
                replace("cluster-id", cluster_id_val)
            try:
                storage_set_count_str = Conf.get(self.index, storage_set_count_key)
            except:
                Log.debug("Validation failed for storage_set_count in %s phase\n" % phase_name)
                raise Exception("Validation failed for storage_set_count in %s phase" % phase_name)

        if storage_set_count_str is not None:
            storage_set_val = int(storage_set_count_str) - 1
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

            """
            Since get_all_keys misses out listing entries inside an array, the
            below code is required to fetch such array entries. The result will
            be stored in a full list which will be complete and will be used to
            verify keys required for each phase.
            """
            arg_keys_list = Conf.get_keys(self.index)
            full_arg_keys_list = []
            for key in arg_keys_list:
                if ((key.find('[') != -1) and (key.find(']') != -1)):
                    storage_set = Conf.get(self.index, key)
                    base_key = key
                    for set_key in storage_set:
                        key = base_key + ">" + set_key
                        full_arg_keys_list.append(key)
                else:
                    full_arg_keys_list.append(key)

            for key in full_arg_keys_list:
                self._key_value_verify(key,phase_name)

            if set(yardstick_list_exp).issubset(set(full_arg_keys_list)):
                Log.debug("%s - keys validation complete\n" % phase_name.lower())
            else:
                Log.debug("Validation failed\n")
                raise Exception("Validation failed for %s" % phase_name)

        except OpenldapSetupError as e:
            raise OpenldapSetupError({"message":"ERROR : Validating keys \
                failed"})

    def post_install(self):
        """ Performs post install operations. Raises exception on error """

        phase_name = "post_install"
        Log.debug("%s - Starting\n" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        Log.debug("%s - Successful" % phase_name)
        # Perform actual operation. Obtain inputs using Conf.get(index, ..)
        return 0

    def prepare(self):
        """ Perform prepare operations. Raises exception on error """

        phase_name = "prepare"
        Log.debug("%s - Starting\n" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        Log.debug("%s - Successful" % phase_name)
        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def config(self):
        """ Performs configurations. Raises exception on error """
        phase_name = "config"
        Log.debug("%s - Starting\n" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        from configcmd import ConfigCmd
        ConfigCmd(self.url).process()
        Log.debug("%s - Successful" % phase_name)
        return 0

    def init(self):
        """ Perform initialization. Raises exception on error """

        phase_name = "init"
        Log.debug("%s - Starting\n" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name)
        Log.debug("%s - Successful" % phase_name)
        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def test(self, plan, config: str):
        """ Perform configuration testing. Raises exception on error """
        phase_name = "test"
        Log.debug("%s - Starting\n" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name) 
        Test(config, "seagate")
        Log.debug("%s - Successful" % phase_name)
        return 0

    def reset(self):
        """ Performs Configuraiton reset. Raises exception on error """

        phase_name = "reset"
        Log.debug("%s - Starting\n" % phase_name)
        self.validate(phase_name)
        self._keys_validate(phase_name) 
        from resetcmd import ResetCmd
        ResetCmd().process()
        Log.debug("%s - Successful" % phase_name)
        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0
