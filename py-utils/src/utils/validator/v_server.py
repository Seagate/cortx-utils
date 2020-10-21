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

import errno

from cortx.utils.validator.error import VError
from cortx.utils.validator.validator_utils import Pillar, NetworkValidations
from cortx.utils.process import SimpleProcess


class ServerV:
    """ Server related validations """

    def validate(self):
        """ Process server valiations """

        controllers = ['primary_mc', 'secondary_mc']
        for controller in controllers:
            result = Pillar.get_pillar(
                f"storage_enclosure:controller:{controller}:ip")
            if result['ret_code']:
                raise Exception(
                    errno.ENOENT, f"{controller} is not set in pillars")
            result = NetworkValidations.check_ping(result['response'])
            if result['ret_code']:
                raise Exception(errno.ECONNREFUSED,
                                "Ping to Controller failed")
        return

    def verify_nodes_online(self):
        """ Check if nodes are online """

        res = Pillar.get_pillar("cluster:node_list")
        if res['ret_code']:
            raise Exception(errno.ENOENT, "Nodes not found in pillars")
        for node in res['response']:
            res = NetworkValidations.check_ping(node)
            if res['ret_code']:
                raise Exception(errno.ECONNREFUSED,
                                f"Pinging node {node} failed")
        return

    def verify_node_communication(self):
        """ validation salt  test.ping """

        res = Pillar.get_pillar("cluster:node_list")
        if res['ret_code']:
            raise Exception(errno.ENOENT, "Nodes not found in pillars")

        for node in res['response']:
            cmd_proc = SimpleProcess(f"salt {node} test.ping --out=json")
            output, err, return_code = cmd_proc.run(timeout=10)

            if return_code:
                raise Exception(errno.ECONNREFUSED,
                                f"Failed to communicate to {node}")
        return

    def verify_passwordless(self):
        """ Passwordless validations """

        res = Pillar.get_hostnames()
        if res['ret_code']:
            raise Exception(errno.ENOENT, "Hosts not found in pillars")

        for node in res['response']:
            cmd_proc = SimpleProcess(f"ssh {node} exit")
            output, err, return_code = cmd_proc.run()

            if return_code:
                raise Exception(errno.ECONNREFUSED,
                                f"No Passwordless ssh: {node}")
        return
