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

import asyncio

from cortx.utils.support.support_bundle import SupportBundle
from cortx.utils.cli_framework.command import Command
from cortx.utils.log import Log


class SupportBundleCli:
    @staticmethod
    def generate(comment: str, **kwargs):
        Log.init('support_bundle', '/var/log/cortx/utils/support', level='INFO',
            backup_count=5, file_size_in_mb=5)

        components = ''
        for key, value in kwargs.items():
            if key == 'components':
                components = value

        options = {'comment': comment,'components':components, 'comm': \
            {'type': 'direct', 'target': 'utils.support', 'method': \
            'generate_bundle', 'class': 'SupportBundle', 'is_static': True, \
            'params': {}, 'json': {}}, 'output': {}, 'need_confirmation': \
            False, 'sub_command_name': 'generate_bundle'}

        cmd_obj = Command('generate_bundle', options, [])
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(SupportBundle.generate_bundle(cmd_obj))
        return res

    @staticmethod
    def get_status(bundle_id: str):
        # status
        import time
        time.sleep(5)

        options = {'bundle_id': bundle_id, 'comm': {'type': 'direct', \
            'target': 'utils.support', 'method': 'get_bundle_status', \
            'class': 'SupportBundle', 'is_static': True, 'params': {}, \
            'json': {}}, 'output': {}, 'need_confirmation': False, \
            'sub_command_name': 'get_bundle_status'}

        cmd_obj = Command('get_bundle_status', options, [])
        loop = asyncio.get_event_loop()
        res = loop.run_until_complete(SupportBundle.get_bundle_status(cmd_obj))
        loop.close()
        return res


if __name__ == '__main__':
    # componets parameter is optional, if not specified support bundle
    # will be created for all components. You can specify multiple
    # components like components = ['utils', 'provisioner']
    bundle_obj = SupportBundleCli.generate(comment= \
        'Support Bundle generation')
    print(bundle_obj)
    bundle_id = str(bundle_obj).split('|')[1].strip()
    status = SupportBundleCli.get_status(bundle_id=bundle_id)
    print(status)