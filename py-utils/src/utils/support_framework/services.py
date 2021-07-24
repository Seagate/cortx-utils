#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
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

import provisioner
import provisioner.freeze
from cortx.utils.log import Log
from cortx.utils.errors import BaseError


class PackageValidationError(BaseError):
    pass

class ProvisionerServices:
    """
    TODO: Class can be removed when Remote communication framework is done
    Added this functionality so there will be no dependecy on CSM.

    "username" and "password" is used for authorization of Provisioner
    api.

    For that, Create the linux user and add the user to "prvsnrusers" group.

    If a fulstack cortx deployed system, then from constore use:
    username from key cortx>software>csm>user
    password from key cortx>software>csm>secret
    """

    def __init__(self):
        try:
            self.provisioner = provisioner
            Log.info("Provisioner plugin is loaded")
            self.provisioner.auth_init(
                username="<username>",
                password="<password>",
                eauth="pam"
            )
        except Exception as error:
            self.provisioner = None
            Log.error(f"Provisioner module not found : {error}")

    async def begin_bundle_generation(self, command_args, target_node_id):
        """
        Execute Bundle Generation via Salt Script.
        :param command_args: Arguments to be parsed to Bundle Generate Command. :type: String
        :param target_node_id: Node_id for target node intended. :type: String
        :return:
        """
        if not self.provisioner:
            raise PackageValidationError("Provisioner is not instantiated.")
        try:
            Log.debug(f"Invoking Provisioner command run with "
                      f"arguments --> cmd_name=cortxcli "
                      f"cmd_args={repr(command_args)} "
                      f"targets={target_node_id}")
            return self.provisioner.cmd_run(cmd_name='cortxcli',
                cmd_args=str(command_args), targets=target_node_id, nowait=True)
        except self.provisioner.errors.ProvisionerError as e:
            Log.error(f"Command Execution error: {e}")
            raise PackageValidationError(f"Command Execution error: {e}")
