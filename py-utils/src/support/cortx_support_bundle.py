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


import errno
import argparse
import inspect
import sys
import os
import traceback
from argparse import RawTextHelpFormatter

from cortx.utils.conf_store import MappedConf
from cortx.utils.support_framework import const
from cortx.utils.const import CLUSTER_CONF_LOG_KEY
from cortx.utils.support_framework import SupportBundle


class CortxSupportBundle:

    """CLI for the Support Bundle Framework."""

    @staticmethod
    def generate(args):
        """Generates support bundle for specified components."""
        from cortx.utils.support_framework.errors import BundleError
        if not args.message:  # no message provided
            raise BundleError("Please provide message, Why you are generating \
                Support Bundle!")
        message = args.message[0]
        bundle_id = args.bundle_id[0]
        path = args.location[0]
        duration = args.duration
        size_limit = args.size_limit.upper()
        # size_limit should be in units - KB, MB or GB.
        units = ['KB', 'MB', 'GB']
        sb_size_unit = any(unit in size_limit for unit in units)
        if not sb_size_unit:
            sys.stderr.write("Support Bundle size limit should be in KB/MB/GB units.\n")
            sys.exit(1)
        binlogs = args.binlogs
        coredumps = args.coredumps
        stacktrace = args.stacktrace
        components = args.modules

        # Use default cortx conf url ('yaml:///etc/cortx/cluster.conf'),
        # if not conf_url is parsed.
        config_url = args.cluster_conf_path[0] if args.cluster_conf_path else const.DEFAULT_CORTX_CONF
        if 'file://' not in path:
            sys.stderr.write(" Target path should be in file format.\n"
                "Please specify the absolute target path.\n"
                "For example:-\n"
                "support_bundle generate -m 'test_cortx' -b 'abc' -t file:///var/cortx/support_bundle\n")
            sys.exit(1)
        path = path.split('//')[1]
        os.makedirs(const.SB_PATH, exist_ok=True)
        bundle_obj = SupportBundle.generate(comment=message, target_path=path,
            bundle_id=bundle_id, duration=duration, config_url=config_url,
            size_limit=size_limit, binlogs=binlogs, coredumps=coredumps,
            stacktrace=stacktrace, components=components)

        display_string_len = len(bundle_obj.bundle_id) + 4
        response_msg = (
            f"Please use the below bundle id for checking the status of support bundle."
            f"\n{'-' * display_string_len}"
            f"\n| {bundle_obj.bundle_id} |"
            f"\n{'-' * display_string_len}"
            f"\nPlease Find the file on -> {bundle_obj.bundle_path} .\n")
        return response_msg

    @staticmethod
    def get_status(args):
        """Get status of generated support bundle."""
        bundle_id = args.bundle_id[0] if args.bundle_id else None
        status = SupportBundle.get_status(bundle_id=bundle_id)
        return status


class GenerateCmd:

    """Get Generate Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser(
            'generate',
            help="generates suppport bundle for nodes.\n"
                "Example command:\n"
                "#$ cortx_support_bundle generate generate -c <conf URL> -t <target URL> -b <bundle_id> -m <message>\n"
                "For more help checkout cortx_support_bundle generate -h\n\n")
        s_parser.set_defaults(func=CortxSupportBundle.generate)
        s_parser.add_argument('-c', '--cluster_conf_path', nargs='+', default='', \
            help='Optional, Location- CORTX confstore file location.')
        s_parser.add_argument('-t', '--location', nargs='+', required=True, \
            help="Location- CORTX support bundle will be generated at specified location.")
        s_parser.add_argument('-b', '--bundle_id', nargs='+', required=True, \
            help='Bundle ID for Support Bundle')
        s_parser.add_argument('-m', '--message', nargs='+', required=True, \
            help='Message - Reason for generating Support Bundle')
        s_parser.add_argument('-d', '--duration', default='P5D',
            help="Duration - duration for which log should be captured, Default - P5D")
        s_parser.add_argument('--size_limit', default='500MB',
            help="Size Limit - Support Bundle size limit per node, Default - 500MB")
        s_parser.add_argument('--binlogs', type=str2bool, default=False,
            help="Include/Exclude Binary Logs, Default = False")
        s_parser.add_argument('--coredumps', type=str2bool, default=False,
            help="Include/Exclude Coredumps, Default = False")
        s_parser.add_argument('--stacktrace', type=str2bool, default=False,
            help="Include/Exclude stacktrace, Default = False")
        s_parser.add_argument('--modules',
            help="list of components & services to generate support bundle.")


class StatusCmd:

    """Get Status Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser(
            'get_status',
            help="Get status of generated suppport bundle.\n"
                "bundle_id is optional, if bundle id is specified, only specified\n"
                "support bundle status is fetched else will fetch all generated support bundle status.\n\n"
                "Example command:\n"
                "#$ cortx_support_bundle get_status -b 'SBag8s1f10' #Fetch status of SBag8s1f10\n"
                "#$ cortx_support_bundle get_status #Fetch status of all support bundles\n\n"
                "For more help checkout cortx_support_bundle get_status -h\n\n")
        s_parser.set_defaults(func=CortxSupportBundle.get_status)
        s_parser.add_argument('-b', '--bundle_id', nargs='+', default='', \
            help='Bundle ID of generated Support Bundle')
        s_parser.add_argument('-c', '--cluster_conf_path', nargs='+', default='', \
            help='Optional, Location- CORTX confstore file location.')

def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('true'):
        return True
    elif value.lower() in ('false'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    from cortx.utils.log import Log
    from cortx.utils.conf_store import Conf

    # Setup Parser
    parser = argparse.ArgumentParser(description='Cortx Support Bundle Interface', \
        formatter_class=RawTextHelpFormatter)
    sub_parser = parser.add_subparsers(title='command', \
        help='represents the action from: generate, get_status\n\n', \
        dest='command')

    # Add Command Parsers
    members = inspect.getmembers(sys.modules[__name__])
    for name, cls in members:
        if name != "Cmd" and name.endswith("Cmd"):
            cls.add_args(sub_parser)

    # Parse and Process Arguments
    try:
        args = parser.parse_args()
        cluster_conf_path = args.cluster_conf_path[0]
        cluster_conf = MappedConf(cluster_conf_path)
        log_path = os.path.join(cluster_conf.get(CLUSTER_CONF_LOG_KEY), \
            f'utils/{Conf.machine_id}/support')
        log_level = cluster_conf.get('utils>log_level', 'INFO')
        Log.init('support_bundle', log_path, level=log_level, backup_count=5, \
            file_size_in_mb=5)
        out = args.func(args)
        if out is not None and len(out) > 0:
            print(out)
        return 0

    except Exception as e:
        sys.stderr.write("%s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        return errno.EINVAL


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)