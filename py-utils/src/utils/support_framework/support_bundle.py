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
import re
import shutil
import psutil
import time
import json
from datetime import datetime, timedelta

from cortx.utils.log import Log
from cortx.utils.schema.providers import Response
from cortx.utils.errors import OPERATION_SUCESSFUL, ERR_OP_FAILED
from cortx.utils.conf_store.conf_store import Conf
from cortx.utils.common.common import ConfigStore
from cortx.utils.cli_framework.command import Command
from cortx.utils.support_framework import const
from cortx.utils.support_framework import Bundle
from cortx.utils.support_framework.bundle_generate import ComponentsBundle
from cortx.utils.support_framework.errors import BundleError
from cortx.utils.process import SimpleProcess


class SupportBundle:

    """This Class initializes the Support Bundle Generation for CORTX."""

    @staticmethod
    def _generate_bundle_id():
        """Generate Unique Bundle ID."""
        alphabet = string.ascii_lowercase + string.digits
        return f"SB{''.join(random.choices(alphabet, k=8))}"

    @staticmethod
    def get_component_size_limit(size_limit, num_components):
        """Returns the size limit per component."""
        units = ['GB', 'MB', 'KB']
        for suffix in units:
            if size_limit.endswith(suffix):
                num_units = size_limit[:-len(suffix)]
                try:
                    size_limit_per_comp = (int(float(num_units)) / num_components)
                    size_limit_per_comp = str(size_limit_per_comp) + suffix
                except ValueError as e:
                    Log.error(f"Failed to get size_limit per component for SB. ERROR:{str(e)}")
                    return None
        return size_limit_per_comp

    @staticmethod
    async def _generate_bundle(command):
        """
        Initializes the process for Generating Support Bundle at shared path.
        command:    Command Object :type: command
        return:     None.
        """
        # Get Arguments From Command
        bundle_id = command.options.get(const.SB_BUNDLE_ID)
        comment = command.options.get(const.SB_COMMENT)
        duration = command.options.get(const.SB_DURATION)
        size_limit = command.options.get(const.SB_SIZE)
        config_url = command.options.get('config_url')
        config_path = config_url.split('//')[1] if '//' in config_url else ''
        path = command.options.get('target_path')
        bundle_path = os.path.join(path, bundle_id)
        try:
            os.makedirs(bundle_path)
        except FileExistsError:
            raise BundleError(errno.EINVAL, "Bundle ID already exists,"
                "Please use Unique Bundle ID")

        cortx_config_store = ConfigStore(config_url)
        # Get Node ID
        node_id = Conf.machine_id
        if node_id is None:
            raise  BundleError(errno.EINVAL, "Invalid node_id: %s", \
                node_id)
        # Update SB status in Filestore.
        # load conf for Support Bundle
        Conf.load(const.SB_INDEX, 'json://' + const.FILESTORE_PATH, skip_reload = True)
        data = {
            'status': 'In-Progress',
            'start_time': datetime.strftime(
                datetime.now(), '%Y-%m-%d %H:%M:%S')
        }
        Conf.set(const.SB_INDEX, f'{node_id}>{bundle_id}', data)
        Conf.save(const.SB_INDEX)

        node_name = cortx_config_store.get(f'node>{node_id}>name')
        Log.info(f'Starting SB Generation on {node_id}:{node_name}')
        components = cortx_config_store.get(f'node>{node_id}>components')
        num_components = len(components)
        # Get required SB size per component
        size_limit_per_comp = SupportBundle.get_component_size_limit(size_limit, num_components)
        components_list = []
        service_per_comp = {}
        for comp_idx in range(0, num_components):
            services = cortx_config_store.get(
                    f'node>{node_id}>components[{comp_idx}]>services')
            service = 'all' if services is None else ','.join(services)
            comp_name = components[comp_idx]['name']
            components_list.append(comp_name)
            service_per_comp[comp_name] = service
        if components is None:
            Log.warn(f"No component specified for {node_name} in CORTX config")
            Log.warn(f"Skipping SB generation on node:{node_name}.")
            return
        bundle_obj = Bundle(bundle_id=bundle_id, bundle_path=bundle_path, \
            comment=comment,node_name=node_name, components=components_list,
            services=service_per_comp)

        # Start SB Generation on Node.
        # Adding CORTX manifest data inside support Bundle.
        try:
            # Copying config file into support bundle.
            common_locations = set()
            if config_path and os.path.exists(config_path):
                Log.info(f'For manifest data collection, taking config from \
                    {config_path} location.')
                # Remove secrets from the input config.
                conf_name = config_path.split('/')[-1]
                sb_config = config_path.replace(conf_name, 'sb_cluster.conf')
                with open(sb_config, 'w+') as sb_file:
                    with open(config_path, 'r' ) as f:
                        content = f.read()
                        if 'secret:' in content:
                            content = re.sub(r'secret:.+',r'secret: ****', content)
                        sb_file.write(content)
                conf_target = os.path.join(bundle_path, 'common' + config_path)
                os.makedirs(conf_target.replace(f'/{conf_name}', ''), exist_ok = True)
                shutil.move(sb_config, conf_target)
                common_locations.add(config_path.split('/')[1])

            # Copying "/etc/cortx/solution" directory into support bundle
            # except for "secret" folder.
            sln_target = os.path.join(bundle_path, 'common' + const\
                .CORTX_SOLUTION_DIR)
            if os.path.exists(sln_target):
                shutil.rmtree(sln_target)
            if os.path.exists(const.CORTX_SOLUTION_DIR):
                _ = shutil.copytree(const.CORTX_SOLUTION_DIR, sln_target, \
                        ignore=shutil.ignore_patterns('secret'))
                common_locations.add(const.CORTX_SOLUTION_DIR.split('/')[1])

            # Copying RELEASE.INFO file into support bundle.
            if os.path.exists(const.CORTX_RELEASE_INFO):
                rel_target = os.path.join(bundle_path, 'common' + const\
                    .CORTX_RELEASE_INFO)
                os.makedirs(rel_target.replace('/RELEASE.INFO', ''), exist_ok = True)
                shutil.copyfile(const.CORTX_RELEASE_INFO, rel_target)
                common_locations.add(const.CORTX_RELEASE_INFO.split('/')[1])
            else:
                Log.warn(f'{const.CORTX_RELEASE_INFO} file not found.')

            # Adding node resources health into the support bundle.
            health_target = os.path.join(bundle_path, 'common' + '/health')
            os.makedirs(health_target, exist_ok = True)
            with open(health_target + '/node_health.json', 'w') as fp:
                info = {}
                info["resource_usage"] = {}
                info["resource_usage"]["cpu_usage"] = SupportBundle.\
                    get_cpu_overall_usage()
                info["resource_usage"]["uptime"] = SupportBundle.\
                    get_system_uptime()
                info["resource_usage"]["disk_usage"] = SupportBundle.\
                    get_disk_overall_usage()
                info["resource_usage"]["memory_usage"] = SupportBundle.\
                    get_mem_overall_usage()
                json.dump(info, fp, indent=4)
            common_locations.add('health')

            try:
                common_path = os.path.join(bundle_path, 'common')
                common_tar = os.path.join(common_path, 'common.tar.gz')
                with tarfile.open(common_tar, "w:gz") as tar:
                    if os.path.exists(common_path):
                        tar.add(common_path, arcname='common')

                # Deleting untar directories from the common folder.
                for location in common_locations:
                    untar_location = os.path.join(common_path, location)
                    if os.path.exists(untar_location):
                        shutil.rmtree(untar_location)
            except (OSError, tarfile.TarError) as err:
                Log.error("Facing issues while adding manifest data into common "
                "directory: {0}".format(err))

        except BundleError as be:
            Log.error(f"Failed to add CORTX manifest data inside Support Bundle.{be}")

        try:
            await ComponentsBundle.init(bundle_obj, node_id, config_url,
                duration=duration, size_limit=size_limit_per_comp)
        except BundleError as be:
            Log.error(f"Bundle generation failed.{be}")
        except Exception as e:
            Log.error(f"Internal error, bundle generation failed {e}")

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
            status = ''
            node_id = Conf.machine_id
            Conf.load(const.SB_INDEX, 'json://' + const.FILESTORE_PATH, skip_reload = True)
            bundle_id = command.options.get(const.SB_BUNDLE_ID)
            if not bundle_id:
                status = Conf.get(const.SB_INDEX, f'{node_id}')
            else:
                status = Conf.get(const.SB_INDEX, f'{node_id}>{bundle_id}>status')
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
    def generate(comment: str, target_path: str, bundle_id:str, **kwargs):
        """
        Initializes the process for Generating Support Bundle on EachCORTX Node.

        comment:        Mandatory parameter, reason why we are generating
                        support bundle
        components:     Optional paramter, If not specified SB will be generated
                        for all components. You can specify multiple components
                        also Eg: components = ['utils', 'provisioner']
        duration:       Duration in ISO 8601 format,
                        For example: "2020-09-06T05:30:00P5DT3H3S"
                        where '2020-09-06T05:30:00' is the start_time &
                        '5DT3H3S' is the duration in ISO 8601 format: D_H_M_S
                        D: Days, H: Hours, M: Minutes, S: Seconds
                        **NOTE: "P" separates, the start datetime and duration.
                        "T" separated date and time.

        return:         bundle_obj
        """
        config_url = kwargs.get('config_url', '')
        duration = kwargs.get('duration', 'P5D')    # Default duration is 5 days
        size_limit = kwargs.get('size_limit', '500MB') # Default size limit per node is '500MB'
        options = {'comment': comment, 'target_path': target_path, 'bundle_id': bundle_id, \
            'config_url': config_url, 'duration': duration, 'size_limit': size_limit, \
            'comm':{'type': 'direct', 'target': \
            'utils.support_framework', 'method': 'generate_bundle', 'class': \
            'SupportBundle', 'is_static': True, 'params': {}, 'json': {}}, \
            'output': {}, 'need_confirmation': False, 'sub_command_name': 'generate_bundle'}

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
    def get_cpu_overall_usage(index=2, percpu=False):
        """Get CPU usage list."""
        i = 0
        cpu_usage = None
        while i < index:
            cpu_usage = f'{psutil.cpu_percent(interval=None, percpu=percpu)} %'
            time.sleep(1)
            i = i + 1
        return cpu_usage

    @staticmethod
    def get_system_uptime():
        """Get system uptime data."""
        cmd = '/usr/bin/uptime -p'
        system_uptime = SimpleProcess(cmd).run()[0].decode('utf-8').strip()
        # Output: 'up 2 weeks, 2 days, 23 hours, 37 minutes'
        system_uptime = system_uptime.replace('up ', '')
        load_average = psutil.getloadavg()
        # Output: (1.62, 1.45, 0.99)
        load_average = f'{load_average[0]}, {load_average[1]}, {load_average[2]}'
        data = {
            'current_time': time.strftime('%H:%M:%S', time.gmtime()),
            'system_uptime': system_uptime,
            'logged_in_users': f'{len(psutil.users())} users',
            'load_average': load_average
        }
        return data

    @staticmethod
    def get_disk_overall_usage():
        units_factor_GB = 1000000000
        overall_usage = []
        dummy_obj = type('dummy_obj', (object,), {})
        root = dummy_obj()
        root.mountpoint = '/'
        for obj in [root]+psutil.disk_partitions():
	        disk_usage = {
                "volume": obj.mountpoint,
                "totalSpace": str(int(psutil.disk_usage(obj.mountpoint).\
                    total)//int(units_factor_GB)) + ' GB',
                "usedSpace": str(int(psutil.disk_usage(obj.mountpoint).\
                    used)//int(units_factor_GB)) + ' GB',
                "freeSpace": str(int(psutil.disk_usage(obj.mountpoint).\
                    free)//int(units_factor_GB)) + ' GB',
                "diskUsedPercentage": str(psutil.disk_usage(obj.mountpoint).\
                    percent) + ' %',
            }
	        overall_usage.append(disk_usage)
        return overall_usage

    @staticmethod
    def get_mem_overall_usage():
        """Collect & return system memory info in specific format."""
        mem_info = dict(psutil.virtual_memory()._asdict())
        total_memory = {}
        for key, value in mem_info.items():
            if key == 'percent':
                total_memory[key] = f'{value} %'
            else:
                total_memory[key] = f'{value >> 20} MB'

        # total: total physical memory (exclusive swap).

        # available: the memory that can be given instantly to processes
        #   without the system going into swap. This is calculated by summing
        #   different memory values depending on the platform and it is
        #   supposed to be used to monitor actual memory usage in a cross
        #   platform fashion.

        # used: memory used, calculated differently depending on the platform
        #   and designed for informational purposes only. total - free does not
        #   necessarily match used.

        # free: memory not being used at all (zeroed) that is readily available;
        #   note that this doesn’t reflect the actual memory available (use
        #   available instead). total - used does not necessarily match free.

        # active (UNIX): memory currently in use or very recently used, and so it is in RAM.

        # inactive (UNIX): memory that is marked as not used.

        # buffers (Linux, BSD): cache for things like file system metadata.

        # cached (Linux, BSD): cache for various things.

        # shared (Linux, BSD): memory that may be simultaneously accessed by multiple processes.

        # slab (Linux): in-kernel data structures cache.

        mem_overall_usage = {
            "total": total_memory['total'],
            "available": total_memory['available'],
            "used_percent": total_memory['percent'],
            "used": total_memory['used'],
            "free": total_memory['free'],
            "active": total_memory['active'],
            "inactive": total_memory['inactive'],
            "buffers": total_memory['buffers'],
            "cached": total_memory['cached'],
            "shared": total_memory['shared'],
            "slab": total_memory['slab']
        }
        return mem_overall_usage

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