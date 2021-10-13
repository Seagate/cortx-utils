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
import tarfile
import asyncio

from cortx.utils.log import Log
from cortx.utils.schema.providers import Response
from cortx.utils.errors import OPERATION_SUCESSFUL, ERR_OP_FAILED
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.cli_framework.command import Command
from cortx.utils.support_framework import const
from cortx.utils.support_framework import Bundle
from cortx.utils.support_framework.errors import BundleError


class SupportBundle:

    """This Class initializes the Support Bundle Generation for CORTX."""

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
    async def _begin_bundle_generation(bundle_obj):
        tar_dest_file = f'{bundle_obj.bundle_id}.tar.gz'
        dest_path = os.path.join(bundle_obj.bundle_path, tar_dest_file)
        Log.debug(f"Generating Bundle at path:{dest_path}")
        CortxConf.init(cluster_conf=bundle_obj.cluster_conf)
        LOG_DIR = CortxConf.get_storage_path('log')
        LOCAL_DIR = CortxConf.get_storage_path('local')
        try:
            for target in [LOG_DIR, LOCAL_DIR]:
                if os.path.isdir(target):
                    with tarfile.open(dest_path, 'w:gz') as tar_handle:
                        tar_handle.add(target, arcname=os.path.abspath(target))
            bundle_status = ("Successfully generated the support bundle "
                            f"at path: '{dest_path}' !!!")
        except Exception as err:
            msg = f"Failed to generate support bundle. ERROR:{err}"
            Log.error(msg)
            bundle_status = msg
        
        # Update the SB status in conf store
        Conf.load(const.SB_INDEX, 'json://' + const.FILESTORE_PATH, fail_reload=False)
        Conf.set(const.SB_INDEX, f'bundle_db>{bundle_obj.bundle_id}', bundle_status)
        Conf.save(const.SB_INDEX)

    @staticmethod
    async def _generate_bundle(command):
        """
        Initializes the process for Generating Support Bundle at shared path.
        command:    Command Object :type: command
        return:     None.
        """
        # CORTX SB Generation Initialized.
        bundle_status = "CORTX SB Generation is In-Progress"
        bundle_id = SupportBundle._generate_bundle_id()
        # load conf for Support Bundle
        Conf.load(const.SB_INDEX, 'json://' + const.FILESTORE_PATH)
        Conf.set(const.SB_INDEX, f'bundle_db>{bundle_id}', bundle_status)
        Conf.save(const.SB_INDEX)
        
        # Get Arguments From Command
        comment = command.options.get(const.SB_COMMENT)
        components = command.options.get(const.SB_COMPONENTS)
        target_path = command.options.get('target_path')
        cluster_conf = command.option.get('cluster_conf')
        if not components:
            components = []

        bundle_path = os.path.join(target_path, bundle_id)
        os.makedirs(bundle_path)
        
        bundle_obj = Bundle(bundle_id=bundle_id, bundle_path=bundle_path, \
            comment=comment,is_shared=True, cluster_conf=cluster_conf)
        # Create CORTX support Bundle
        try:
            await SupportBundle._begin_bundle_generation(bundle_obj)
        except BundleError as be:
            Log.error(f"Bundle generation failed.{be}")

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
            Conf.load(const.SB_INDEX, 'json://' + const.FILESTORE_PATH)
            bundle_id = command.options.get(const.SB_BUNDLE_ID)
            status = Conf.get(const.SB_INDEX, f'bundle_db>{bundle_id}')
            if not status:
                return Response(output=(f"No status found for bundle_id: {bundle_id}" \
                    "in input config. Please check if the Bundle ID is correct"), \
                    rc=ERR_OP_FAILED)
            return Response(output = status, rc = OPERATION_SUCESSFUL)
        except Exception as e:
            Log.error(f"Failed to get bundle status: {e}")
            return Response(output=(f"Support Bundle status is not available " \
                f"Failed to get status of bundle. Related error - {e}"), \
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
            if key == 'target_path':
                path = value
            if key == 'cluster_conf':
                cluster_conf = value
        options = {'comment': comment, 'components': components, 'target_path': path, \
            'comm':{'type': 'direct', 'target': 'utils.support_framework', 'method': \
            'generate_bundle', 'class': 'SupportBundle', 'is_static': True, \
            'params': {}, 'json': {}}, 'output': {}, 'need_confirmation': \
            False, 'sub_command_name': 'generate_bundle', 'cluster_conf':\
            cluster_conf}

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