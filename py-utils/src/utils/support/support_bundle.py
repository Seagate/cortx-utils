# CORTX-CSM: CORTX Management web and CLI interface.
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

import sys
import string
import random
import getpass
import errno
from cortx.utils.support import const
from cortx.utils.support.model import SupportBundleRepository
from cortx.utils.errors import OPERATION_SUCESSFUL
from cortx.utils.support.errors import BundleError
from cortx.utils.data.db.db_provider import (DataBaseProvider, GeneralConfig)
from cortx.utils.errors import DataAccessExternalError
from cortx.utils.schema.providers import Response
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.log import Log
from cortx.utils.support.services import ProvisionerServices
from cortx.utils.schema import database

class SupportBundle:
    """
    This Class initializes the Support Bundle Generation for CORTX.
    """
    

    @staticmethod
    async def get_active_nodes():
        """
        This Method is for reading hostnames, node_list information.
        :return: hostnames : List of Hostname :type: List
        :return: node_list : : List of Node Name :type: List
        """
        Log.info("Reading hostnames, node_list information")
        Conf.load('cortx_cluster', 'json:///etc/cortx/cluster.conf')
        node_hostname_map = Conf.get('cortx_cluster', 'cluster')
        if not node_hostname_map:
            response_msg = "Node list and hostname not found."
            return Response(output=response_msg,
                            rc=errno.ENODATA), None

        return node_hostname_map

    @staticmethod
    def _generate_bundle_id():
        """Generate Unique Bundle ID."""
        alphabet = string.ascii_lowercase + string.digits
        return f"SB{''.join(random.choices(alphabet, k = 8))}"

    @staticmethod
    def _get_components(components):
        """Get Components to Generate Support Bundle."""
        if components and "all" not in components:
            Log.info(f"Generating bundle for  {' '.join(components)}")
            shell_args = f"{' '.join(components)}"
        else:
            Log.info("Generating bundle for all CORTX components.")
            shell_args = "all"
        return f" -c {shell_args}"

    @staticmethod
    async def generate_bundle(command) -> sys.stdout:
        """
        Initializes the process for Generating Support Bundle on Each CORTX Node.
        :param command: Csm_cli Command Object :type: command
        :return: None.
        """
        current_user = str(getpass.getuser())
        # Check if User is Root User.
        if current_user.lower() != "root":
            response_msg = "Support Bundle Command requires root privileges"
            return Response(output = response_msg, rc = errno.EACCES)
        bundle_id = SupportBundle._generate_bundle_id()
        provisioner = ProvisionerServices()
        if not provisioner:
            return Response(output = "Provisioner package not found.",
                            rc = errno.ENOENT)
        # Get Arguments From Command
        comment = command.options.get(const.SB_COMMENT)
        components = command.options.get(const.SB_COMPONENTS)
        if not components:
            components = []
        if command.options.get(const.SOS_COMP, False) == "true":
            components.append("os")
        comp_list = SupportBundle._get_components(components)

        # Get HostNames and Node Names.
        node_hostname_map = await SupportBundle.get_active_nodes()
        if not isinstance(node_hostname_map, dict):
            return node_hostname_map

        # Start SB Generation on all Nodes.
        for nodename, hostname in node_hostname_map.items():
            Log.debug(f"Connect to {hostname}")
            try:
                await provisioner.begin_bundle_generation(
                    f"bundle_generate '{bundle_id}' '{comment}' "
                    f"'{hostname}' {comp_list}", nodename)
            except BundleError as be:
                Log.error(f"Bundle generation failed.{be}")
                return Response("Bundle generation failed.\nPlease "
                         "check CLI for details.", rc = errno.EINVAL)
            except Exception as e:
                Log.error(f"Provisioner API call failed : {e}")
                return Response(output = "Bundle Generation Failed.",
                                rc = errno.ENOENT)

        symlink_path = const.SYMLINK_PATH
        display_string_len = len(bundle_id) + 4
        response_msg = (
            f"Please use the below bundle id for checking the status of support bundle."
            f"\n{'-' * display_string_len}"
            f"\n| {bundle_id} |"
            f"\n{'-' * display_string_len}"
            f"\nPlease Find the file on -> {symlink_path} .\n")

        return Response(output = response_msg,
                        rc = OPERATION_SUCESSFUL)

    @staticmethod
    async def get_bundle_status(command):
        """
        Initializes the process for Displaying the Status for Support Bundle.
        :param command: Csm_cli Command Object :type: command
        :return: None
        """
        try:
            bundle_id = command.options.get(const.SB_BUNDLE_ID)
            conf = GeneralConfig(database.DATABASE)
            db = DataBaseProvider(conf)
            repo = SupportBundleRepository(db)
            all_nodes_status = await repo.retrieve_all(bundle_id)
            response = {"status": [each_status.to_primitive() for each_status in
                               all_nodes_status]}
            return Response(output = response, rc = OPERATION_SUCESSFUL)
        except DataAccessExternalError as e:
            Log.warn(f"Failed to connect to elasticsearch: {e}")
            return Response(output = ("Support Bundle status is not available currently"
                " as required services are not running."
                " Please wait and check the /tmp/support_bundle"
                " folder for newly generated support bundle."),
                            rc = str(errno.ECONNREFUSED))
        except Exception as e:
            Log.error(f"Failed to get bundle status: {e}")
            return Response(output = ("Support Bundle status is not available currently"
                " as required services are not running."
                " Failed to get status of bundle."),
                            rc = str(errno.ENOENT))
