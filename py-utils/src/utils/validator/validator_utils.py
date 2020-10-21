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

import json

from cortx.utils.process import SimpleProcess


class Pillar:

    @staticmethod
    def get_pillar(key):
        """Get pillar data for key"""
        cmd = f"salt-call pillar.get {key} --out=json"
        cmd_proc = SimpleProcess(cmd)
        output, err, return_code = cmd_proc.run()
        if return_code == 127:
            message = "get_pillar: salt-call: command not found"
        elif return_code == 0:
            res = json.loads(output)
            res = res['local']
            if not res:
                message = f"get_pillar: No pillar data for key: {key}"
                err = f"No pillar data for key: {key}"
                return_code = 1
            else:
                output = res
                message = f"pillar data {res}"
        else:
            message = "get_pillar: Failed to get pillar data"
        return {"ret_code": return_code,
                "response": output,
                "error_msg": err,
                "message": message}

    @staticmethod
    def get_hostnames():
        res = Pillar.get_pillar("cluster:node_list")
        if res['ret_code']:
            return res
        hostnames = []
        for node in res['response']:
            res = Pillar.get_pillar(f"cluster:{node}:hostname")
            if res['ret_code']:
                return res
            hostnames.append(res['response'])
        res['response'] = hostnames
        return res


class NetworkValidations:

    @staticmethod
    def check_ping(ip):
        """ Check if IP's are reachable """

        cmd = f"ping -c 1 {ip}"
        cmd_proc = SimpleProcess(cmd)
        output, err, return_code = cmd_proc.run()
        if return_code == 0:
            message = f"{ip} is reachable"
        elif return_code == 1:
            message = f"check_ping: {ip}: Destination Host Unreachable"
        elif return_code == 2:
            message = f"check_ping: {ip}: Name or service not known"
        else:
            message = f"check_ping: {ip}: Not reachable"
        return {"ret_code": return_code,
                "response": output,
                "error_msg": err,
                "message": message}
