#!/bin/env python3

# CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
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
import errno

from cortx.utils.validator.error import VError
from cortx.utils.validator.validator_utils import Pillar, NetworkValidations

class NetworkV:
    """ Network related validations """
    def __init__(self):
        # TODO: Perform initialization for network level commands
        pass

    def validate(self, args):
        """ Process network valiations """

        if not isinstance(args, list) or len(args) < 1:
            raise VError(errno.EINVAL, "Invalid parameters %s" %args)

        action = args[0]

        # TODO Write actual code here
        if action == "iface": 
            self.validate_iface(args[1])
        elif action == "management_vip":
            self.verify_management_vip()
        elif action == "cluster_ip":
            self.verify_cluster_ip()
        elif action == "public_data_ip":
            self.verify_public_data_ip()
        elif action == "private_data_ip":
            self.verify_private_data_ip()

    def validate_iface(self, iface):
        # TODO: This is sample. Need to add actual network validation
        
        iface_list = os.listdir("/sys/class/net/")
        if iface in iface_list:
            return

        raise Exception(errno.ENOENT, "No such interface %s" %iface)

    def verify_management_vip(self):
        """ Validations for Management VIP """

        res = Pillar.get_pillar("cluster:mgmt_vip")
        if res['ret_code']:
            raise Exception(errno.ENOENT, "Management VIP is not set in pillars")
        else:
            res = NetworkValidations.check_ping(res['response'])
            if res['ret_code']:
                raise Exception(errno.ECONNREFUSED, "Ping to Management VIP failed")
        return

    def verify_cluster_ip(self):
        """ Validations for Cluster IP """

        res = Pillar.get_pillar("cluster:cluster_ip")
        if res['ret_code']:
            raise Exception(errno.ENOENT, "Cluster IP is not set in pillars")
        else:
            res = NetworkValidations.check_ping(res['response'])
            if res['ret_code']:
                raise Exception(errno.ECONNREFUSED, "Ping to Cluster IP failed")
        return

    def verify_public_data_ip(self):
        """ Validations for public data ip """

        res = Pillar.get_pillar("cluster:node_list")
        if not res['ret_code']:
            nodes = res['response']
            for node in nodes:
                result = Pillar.get_pillar(f"cluster:{node}:network:data_nw:public_ip_addr")
                if result['ret_code']:
                    raise Exception(errno.ENOENT, f"Public data IP for {node} is not set in pillars")
                result = NetworkValidations.check_ping(result['response'])
                if result['ret_code']:
                    raise Exception(errno.ECONNREFUSED, f"Ping to Public data IP for {node} failed")
        return

    def verify_private_data_ip(self):
        """ Validations for private data ip """

        res = Pillar.get_pillar("cluster:node_list")
        if not res['ret_code']:
            nodes = res['response']
            for node in nodes:
                result = Pillar.get_pillar(f"cluster:{node}:network:data_nw:pvt_ip_addr")
                if result['ret_code']:
                    raise Exception(errno.ENOENT, f"Private data IP for {node} is not set in pillars")
                result = NetworkValidations.check_ping(result['response'])
                if result['ret_code']:
                    raise Exception(errno.ECONNREFUSED, f"Ping to Private data IP for {node} failed")
        return
