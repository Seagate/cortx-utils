#!/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

import re

def get_cmd_error_msg(msg:str, cmd:str=None, result:list=None):
    msg = f"\n{80*'*'}\nMessage:\t{msg}\n"

    if cmd:
        msg += f"Command:\t\"{cmd}\"\n"

    if result:
        if isinstance(result, list):
            for i in range(2):
                if not isinstance(result[i], str):
                    result[i] = result[i].decode("utf-8")

            msg += f"Return Code:\t'{result[2]}'\n"
            if result[1]:
                msg += "Error:"

                err_msgs = re.split('\r|\n', result[1])
                for err_msg in err_msgs:
                    if err_msg:
                        msg += f"\t\t'{err_msg}'\n"

            if result[0]:
                msg += "Output:"
                other_msgs = re.split('\r|\n', result[0])
                for other_msg in other_msgs:
                    if other_msg:
                        msg += f"\t\t'{other_msg}'\n"

        else:
            msg += f"Result:\t\"{result}\"\n"

    msg += f"{80*'*'}\n"

    return msg
