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
# please email opensource@seagate.com or cortx-questions@seagate.com

import os
import errno
import string
import random
import asyncio

from cortx.utils.log import Log
from cortx.utils.schema import database
from cortx.utils.shared_storage import Storage
from cortx.utils.schema.providers import Response
from cortx.utils.errors import OPERATION_SUCESSFUL
from cortx.utils.schema.payload import Tar
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.cli_framework.command import Command
from cortx.utils.errors import DataAccessExternalError
from cortx.utils.support_framework import const
from cortx.utils.support_framework import Bundle
from cortx.utils.support_framework.errors import BundleError
from cortx.utils.support_framework.services import ProvisionerServices
from cortx.utils.support_framework.model import SupportBundleRepository
from cortx.utils.support_framework.bundle_generate import ComponentsBundle
from cortx.utils.data.db.db_provider import (DataBaseProvider, GeneralConfig)
from cortx.utils.common import CortxConf


class SupportBundle:

    """This Class initializes the Support Bundle Generation for CORTX."""

    @staticmethod
    async def _get_active_nodes() -> dict:
        """This Method is for reading hostnames, node_list information

        Returns:
            dict:     hosts in cluster eg {node1:fqd1}
            Response: Response object if no host found in config file
        """
        Log.info("Reading hostnames, node_list information")
        Conf.load('cortx_cluster', 'json:///etc/cortx/cluster.conf', \
            skip_reload=True)
        node_hostname_map = Conf.get('cortx_cluster', 'cluster')
        if not node_hostname_map:
            response_msg = "Node list and hostname not found."
            return Response(output=response_msg, rc=errno.ENODATA), None
        return node_hostname_map

    @staticmethod
    def _generate_bundle_id():
        """Generate Unique Bundle ID."""
        alphabet = string.ascii_lowercase + string.digits
        return f"SB{''.join(random.choices(alphabet, k=8))}"

    @staticmethod
    def _get_components(components):
        """Get Components to Generate Support Bundle."""
        if components and 'all' not in components:
            Log.info(f"Generating bundle for  {' '.join(components)}")
            shell_args = f"{' '.join(components)}"
        else:
            Log.info("Generating bundle for all CORTX components.")
            shell_args = 'all'
        return f" -c {shell_args}"

    @staticmethod
    async def _generate_bundle(command):
        """
        Initializes the process for Generating Support Bundle on Each CORTX Node.

        command:    Command Object :type: command
        return:     None.
        """
        bundle_id = SupportBundle._generate_bundle_id()
        provisioner = ProvisionerServices()
        if not provisioner:
            return Response(output="Provisioner package not found.", \
                rc=errno.ENOENT)
        # Get Arguments From Command
        comment = command.options.get(const.SB_COMMENT)
        components = command.options.get(const.SB_COMPONENTS)
        if not components:
            components = []
        if command.options.get(const.SOS_COMP, False) == 'true':
            components.append('os')
        # Get HostNames and Node Names.
        node_hostname_map = await SupportBundle._get_active_nodes()
        if not isinstance(node_hostname_map, dict):
            return node_hostname_map

        shared_path = Storage.get_path(name='support_bundle')
        path = shared_path if shared_path else \
            CortxConf.get_key('support>local_path')

        bundle_path = os.path.join(path,bundle_id)
        os.makedirs(bundle_path)
        
        bundle_obj = Bundle(bundle_id=bundle_id, bundle_path=path, \
            comment=comment,is_shared=True if shared_path else False)
        
        support_bundle_file = os.path.join(Conf.get('cortx_conf', 'install_path'),\
            'cortx/utils/conf/support_bundle.yaml')
        Conf.load('sb_yaml', f'yaml://{support_bundle_file}', skip_reload=True)
        all_components = Conf.get('sb_yaml', 'COMPONENTS')
        invalid_comps = [component for component in components if component not in all_components.keys()]
        if invalid_comps:
            components = list(set(components) - set(invalid_comps))
            ComponentsBundle._publish_log(f"""Invalid components - '{", ".join(invalid_comps)}'""", \
                'error', bundle_id, '', comment)
        if invalid_comps and not components:
            return bundle_obj
        comp_list = SupportBundle._get_components(components)

        # Start SB Generation on all Nodes.
        for nodename, hostname in node_hostname_map.items():
            Log.debug(f"Connect to {hostname}")
            try:
                # TODO: pass bundle_path to bundle_generation when args implemented
                await provisioner.begin_bundle_generation(
                    f"bundle_generate '{bundle_id}' '{comment}' "
                    f"'{hostname}' {comp_list}", nodename)
            except BundleError as be:
                Log.error(f"Bundle generation failed.{be}")
                ComponentsBundle._publish_log(f"Bundle generation failed.{be}", \
                    'error', bundle_id, nodename, comment)
            except Exception as e:
                Log.error(f"Internal error, bundle generation failed {e}")
                ComponentsBundle._publish_log(f"Internal error, bundle generation failed \
                    {e}", 'error', bundle_id, nodename, comment)

        # Create common tar.
        #if bundle_obj.is_shared:
        #    tar_dest_file = f"{bundle_id}.tar.gz"
        #    Log.debug(f"Merging all bundle to {bundle_path}/{tar_dest_file}")
        #    try:
        #        Tar(os.path.join(bundle_path, tar_dest_file)).dump([bundle_path])
        #    except:
        #        Log.debug("Merging of node support bundle failed")
        #        return Response(output="Bundle Generation Failed in merging",
        #        rc=errno.EINVAL)
        if command.sub_command_name == 'generate':
            display_string_len = len(bundle_obj.bundle_id) + 4
            response_msg = (
            f"Please use the below bundle id for checking the status of support bundle."
            f"\n{'-' * display_string_len}"
            f"\n| {bundle_obj.bundle_id} |"
            f"\n{'-' * display_string_len}"
            f"\nPlease Find the file on -> {bundle_obj.bundle_path} .\n")
            return Response(output=response_msg, rc=OPERATION_SUCESSFUL)
        return bundle_obj

    @staticmethod
    async def _get_bundle_status(command):
        """
        Initializes the process for Displaying the Status for Support Bundle.

        command:    Command Object :type: command
        return:     None
        """
        try:
            bundle_id = command.options.get(const.SB_BUNDLE_ID)
            conf = GeneralConfig(database.DATABASE)
            db = DataBaseProvider(conf)
            repo = SupportBundleRepository(db)
            all_nodes_status = await repo.retrieve_all(bundle_id)
            response = {'status': [each_status.to_primitive() for each_status in
                                   all_nodes_status]}
            return Response(output = response, rc = OPERATION_SUCESSFUL)
        except DataAccessExternalError as e:
            Log.warn(f"Failed to connect to elasticsearch: {e}")
            return Response(output=(f"Support Bundle status is not available " \
                "currently as required services are not running. Please wait " \
                "and check the /tmp/support_bundle folder for newly generated " \
                "support bundle. Related error - Failed to connect to elasticsearch: {e}"), \
                rc=str(errno.ECONNREFUSED))
        except Exception as e:
            Log.error(f"Failed to get bundle status: {e}")
            return Response(output=(f"Support Bundle status is not available " \
                "currently as required services are not running. Failed to " \
                "get status of bundle. Related error - Failed to get bundle status: {e}"), \
                rc=str(errno.ENOENT))

    @staticmethod
    def generate(comment: str, **kwargs):
        """
        Initializes the process for Generating Support Bundle on EachCORTX Node.

        comment:        Mandatory parameter, reason why we are generating
                        support bundle
        components:     Optional paramter, If not specified SB will be generated
                        for all components. You can specify multiple components
                        also Eg: components = ['utils', 'provisioner']
        return:         bundle_obj
        """
        components = ''
        for key, value in kwargs.items():
            if key == 'components':
                components = value
        options = {'comment': comment, 'components': components, 'comm': \
            {'type': 'direct', 'target': 'utils.support_framework', 'method': \
            'generate_bundle', 'class': 'SupportBundle', 'is_static': True, \
            'params': {}, 'json': {}}, 'output': {}, 'need_confirmation': \
            False, 'sub_command_name': 'generate_bundle'}

        cmd_obj = Command('generate_bundle', options, [])
        loop = asyncio.get_event_loop()
        bundle_obj = loop.run_until_complete( \
            SupportBundle._generate_bundle(cmd_obj))
        return bundle_obj

    @staticmethod
    def get_status(bundle_id: str = None):
        """
        Initializes the process for Displaying the Status for Support Bundle

        bundle_id:  Using this will fetch bundle status :type: string
        """
        options = {'bundle_id': bundle_id, 'comm': {'type': 'direct', \
            'target': 'utils.support_framework', 'method': 'get_bundle_status', \
            'class': 'SupportBundle', \
            'is_static': True, 'params': {}, 'json': {}},'output': {},\
            'need_confirmation': False, 'sub_command_name': \
            'get_bundle_status'}

        cmd_obj = Command('get_bundle_status', options, [])
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(
            SupportBundle._get_bundle_status(cmd_obj))
        if res.rc() == OPERATION_SUCESSFUL:
            import json
            return json.dumps(res.output(), indent=2)
        else:
            return res.output()

    @staticmethod
    def delete(bundle):
        if bundle.bundle_id:
            # delete the old generated support bundle based on bundle_id
            pass
        else:
            # Do we need to delete all SB??
            pass

    @staticmethod
    def cancel(bundle):
        if bundle.bundle_id:
            # cancel/stop ongoing SB generation
            # This will delete the collected data so far,
            # even if the bundle generation is complete.
            pass
        else:
            # it will cancel all the support bundle generation in progress
            pass