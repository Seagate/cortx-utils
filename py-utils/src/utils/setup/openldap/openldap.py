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
import BaseError 

from cortx.utils.validator.v_pkg import PkgV
from cortx.utils.validator.v_network import NetworkV
from cortx.utils.conf_store import Conf
from cortx.utils.log import Log

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
    _preqs_conf_file = "openldapsetup_prereqs.json"
    _prov_conf_file = "openldap_prov_config.yaml"

    def __init__(self, conf_url):
        if not os.path.isfile(self._preqs_conf_file):
            raise OpenldapSetupError({"message":"pre-requisite json file \
                not found"})
        Conf.load(self.index, conf_url)
        Conf.load(self.prov, f'yaml://{self._prov_conf_file}')

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
                files = Conf.get(phase, f'{phase}>files')
                if files:
                    PkgV().validate('files', files)
                services = Conf.get(phase, f'{phase}>services')
                if services:
                    PkgV().validate('services', services)
        except OpenldapSetupError as e:
            raise OpenldapSetupError({"message":"prereqs validation failed"})
        return 0

    def _key_value_verify(self, key: str):
        """Verify if there exists a corresponding value for given key."""

        value = Conf.get(self.index, key)
        if not value:
            raise OpenldapSetupError({"message":"Empty value for key"})
        else:
            address_token = ["hostname", "public_fqdn", "private_fqdn"]
            for token in address_token:
                if key.find(token) != -1:
                    NetworkV().validate('connectivity',[value])
                    break

    def _extract_yardstick_list(self, phase_name: str):
        """Extract keylist to be used as yardstick for validating keys."""

        prov_keys_list = Conf.get_keys(self.prov)
        """
        The openldap prov config file has below pairs :
        "Key Constant" : "Actual Key"
        Example of "Key Constant" :
          CONFSTORE_SITE_COUNT_KEY
          PREPARE
          CONFIG>CONFSTORE_LDAPADMIN_USER_KEY
          INIT
        Example of "Actual Key" :
          cluster>cluster-id>site>storage_set_count
          cortx>software>openldap>sgiam>user
        When we call get_all_keys on openldap prov config file, it returns all
        the "Key Constant", which will contain PHASE(name) as the root
        attribute (except for unsolicited keys). To get "Actual Key" from each
        "Key Constant", we need to call get_confkey on every such key.
        Note that for each of these "Key Constant", there may not exist an
        "Actual Key" because some phases do not have any "Actual Key".
        Example of such cases -
          POST_INSTALL
          PREPARE
        For such examples, we skip and continue with remaining keys.
        We have all "Key Constant" in prov_keys_list, now extract "Actual Key"
        if it exists and depending on phase and hierarchy, decide whether it
        should be added to the yardstick list for the phase passed here.
        """
        yardstick_list = []
        prev_phase = True
        next_phase = False
        for key in prov_keys_list:
            """
            If PHASE is not relevant, skip the key. Or set flag as appropriate.
            For test, reset and cleanup, do not inherit keys.
            """
            if next_phase:
                break
            if key.find(phase_name) == 0:
                prev_phase = False
            else:
                if phase_name in ["TEST", "RESET", "CLEANUP"]:
                    continue
                if not prev_phase:
                    next_phase = True
                    break
            value = Conf.get(self.index, key)
            """
            If value does not exist which can be the case for certain phases as
            mentioned above, skip the value.
            """
            if value is None:
                continue
            yardstick_list.append(value)
        return yardstick_list

    def _keys_validate(self, phase_name: str):
        """Validate keys of each phase against argument file."""

        if self.machine_id is not None:
            machine_id_val = self.machine_id
        if self.cluster_id is not None:
            cluster_id_val = self.cluster_id
        """
        The 'storage_set_count' is read using below hard-coded key which is the
        max array size for storage set.
        """
        storage_set_count_key = "cluster>cluster-id>site>storage_set_count"
        if self.cluster_id is not None:
            storage_set_count_key = storage_set_count_key.\
                replace("cluster-id", cluster_id_val)
            storage_set_count_str = Conf.get(self.index, storage_set_count_key)
        if storage_set_count_str is not None:
            storage_set_val = int(storage_set_count_str)
        else:
            storage_set_val = 0
        phase_name = phase_name.upper()
        try:
            yardstick_list = self._extract_yardstick_list(phase_name)

            arg_keys_list = Conf.get_keys(self.index)

            """
            Since get_all_keys misses out listing entries inside an array, the
            below code is required to fetch such array entries. The result will
            be stored in a full list which will be complete and will be used to
            verify keys required for each phase.
            """
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

            """
            Below algorithm uses tokenization of both yardstick and argument
            key based on delimiter to generate smaller key-tokens. Then check
            (A) all the key-tokens are pairs of pre-defined token. e.g., if
                key_yard is machine-id, then key_arg must have corresponding
                value of machine_id_val.
            OR
            (B) both the key-tokens from key_arg and key_yard are the same.
            """
            list_match_found = True
            key_match_found = False
            for key_yard in yardstick_list:
                key_yard_token_list = re.split('>|\[|\]', key_yard)
                key_match_found = False
                for key_arg in full_arg_keys_list:
                    if key_match_found is False:
                        key_arg_token_list = re.split('>|\[|\]', key_arg)
                        if len(key_yard_token_list) == len(key_arg_token_list):
                            for key_x, key_y in \
                                zip(key_yard_token_list, key_arg_token_list):
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
                            if key_match_found:
                                self._key_value_verify(key_arg)
                if key_match_found is False:
                    list_match_found = False
                    break
            if list_match_found is False:
                raise OpenldapSetupError({"message":"No match found for key"})
            Log.debug("Validation complete\n")

        except OpenldapSetupError as e:
            raise OpenldapSetupError({"message":"ERROR : Validating keys \
                failed"})

    def post_install(self):
        """ Performs post install operations. Raises exception on error """

        self.validate("post_install")
        self._keys_validate("post_install")
        # Perform actual operation. Obtain inputs using Conf.get(index, ..)
        return 0

    def init(self):
        """ Perform initialization. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def config(self):
        """ Performs configurations. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def test(self, plan):
        """ Perform configuration testing. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0

    def reset(self):
        """ Performs Configuraiton reset. Raises exception on error """

        # TODO: Perform actual steps. Obtain inputs using Conf.get(index, ..)
        return 0
