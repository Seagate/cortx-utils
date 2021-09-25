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
import traceback
from argparse import RawTextHelpFormatter
from cortx.utils.common.common import CortxConf
from cortx.utils.support_framework import SupportBundle


class SupportBundleCli:

    """CLI for the Support Bundle Framework."""

    @staticmethod
    def generate(args):
        """Generates support bundle for specified components."""
        from cortx.utils.support_framework.errors import BundleError
        if not args.comment:  # no comment provided
            raise BundleError("Please provide comment, Why you are generating \
                Support Bundle!")
        comment = args.comment[0]
        components = args.component[0].split(';') if args.component else []
        bundle_obj = SupportBundle.generate(comment=comment, \
            components=components)
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
            help="generates suppport bundle for specified component.\n"
                "components is optional parameter, if components is not specified\n"
                "support bundle will be generated for all components\n"
                "Example components passed: 'utils', 'utils;csm;provisioner'\n\n"
                "Example command:\n"
                "#$ support_bundle generate 'sample comment'\n"
                "#$ support_bundle generate 'sample comment' -c 'utils'\n"
                "#$ support_bundle generate 'sample comment' -c 'utils;csm'\n\n"
                "For more help checkout support_bundle generate -h\n\n")
        s_parser.set_defaults(func=SupportBundleCli.generate)
        s_parser.add_argument('comment', nargs='+', help='Comment - Reason for generating Support Bundle')
        s_parser.add_argument('-c', '--component', nargs='+', default=[], \
            help='Optional, Specified component support bundle will be generated')


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
                "#$ support_bundle get_status -b 'SBag8s1f10' #Fetch status of SBag8s1f10\n"
                "#$ support_bundle get_status #Fetch status of all support bundles\n\n"
                "For more help checkout support_bundle get_status -h\n\n")
        s_parser.set_defaults(func=SupportBundleCli.get_status)
        s_parser.add_argument('-b', '--bundle_id', nargs='+', default='', \
            help='Bundle ID of generated Support Bundle')


def main():
    from cortx.utils.log import Log
    from cortx.utils.conf_store import Conf

    log_path = CortxConf.get_log_path('support')
    log_level = CortxConf.get_key('utils>log_level', 'INFO')
    Log.init('support_bundle', log_path, level=log_level, backup_count=5, \
        file_size_in_mb=5, syslog_server='localhost', syslog_port=514)
    # Setup Parser
    parser = argparse.ArgumentParser(description='Support Bundle CLI', \
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