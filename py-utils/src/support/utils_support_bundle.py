#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import sys
import os
import shutil
import tarfile
import errno
import argparse

from cortx.utils.errors import UtilsError
from cortx.utils.process import SimpleProcess
from cortx.utils.const import CLUSTER_CONF_LOG_KEY
from cortx.utils.conf_store import Conf, MappedConf


class SupportBundleError(UtilsError):
    """ SupportBundleError exception with error code and output """

    def __init__(self, rc, message, *args):
        super().__init__(rc, message, *args)


class UtilsSupportBundle:
    """ Generate support bundle for py-utils """
    _default_path = '/tmp/cortx/support_bundle/'
    _tar_name = 'py-utils'
    _tmp_src = '/tmp/cortx/py-utils/'

    @staticmethod
    def generate(bundle_id: str, target_path: str, cluster_conf_url: str, **filters):
        """ Generate a tar file. """
        duration = filters.get('duration', 'P5D')
        size_limit = filters.get('size_limit', '500MB')
        binlogs = filters.get('binlogs', False)
        coredumps = filters.get('coredumps', False)
        stacktrace = filters.get('stacktrace', False)
        # TODO process duration, size_limit, binlogs, coredumps and stacktrace
        # Find log dirs
        cluster_conf = MappedConf(cluster_conf_url)
        log_base = cluster_conf.get(CLUSTER_CONF_LOG_KEY)
        local_base = cluster_conf.get('cortx>common>storage>local')
        machine_id = Conf.machine_id

        if os.path.exists(UtilsSupportBundle._tmp_src):
            UtilsSupportBundle.__clear_tmp_files()
        else:
            os.makedirs(UtilsSupportBundle._tmp_src)
        # Copy log files
        shutil.copytree(os.path.join(log_base, f'utils/{machine_id}'),\
            os.path.join(UtilsSupportBundle._tmp_src, 'logs'))

        UtilsSupportBundle.__generate_tar(bundle_id, target_path)
        UtilsSupportBundle.__clear_tmp_files()

    @staticmethod
    def __copy_file(source: str, destination: str = None):
        """ Copy a file from source to destination location """
        directory = os.path.dirname(UtilsSupportBundle._tmp_src)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if destination is None:
            destination = os.path.join(UtilsSupportBundle._tmp_src,
                os.path.basename(source))
        try:
            shutil.copy2(source, destination)
        except FileNotFoundError as fe:
            raise SupportBundleError(errno.ENOENT, "File not found %s", fe)

    @staticmethod
    def __generate_tar(bundle_id: str, target_path: str):
        """ Generate tar.gz file at given path """
        component = 'utils'
        target_path = target_path if target_path is not None \
            else UtilsSupportBundle._default_path
        target_path = os.path.join(target_path, component)
        tar_name = bundle_id if bundle_id else UtilsSupportBundle._tar_name
        tar_file_name = os.path.join(target_path, tar_name + '.tar.gz')
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        with tarfile.open(tar_file_name, 'w:gz') as tar:
            tar.add(UtilsSupportBundle._tmp_src,
                arcname=os.path.basename(UtilsSupportBundle._tmp_src))

    @staticmethod
    def __clear_tmp_files():
        """ Clean temporary files created by the support bundle """
        shutil.rmtree(UtilsSupportBundle._tmp_src)

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='''Bundle utils logs ''')
        parser.add_argument('-b', dest='bundle_id', help='Unique bundle id')
        parser.add_argument('-t', dest='path', help='Path to store the created bundle',
            nargs='?', default="/var/seagate/cortx/support_bundle/")
        parser.add_argument('-c', dest='cluster_conf',\
            help="Cluster config file path for Support Bundle")
        parser.add_argument('-s', '--services', dest='services', nargs='+',\
            default='', help='List of services for Support Bundle')
        parser.add_argument('-d', '--duration', default='P5D', dest='duration',
            help="Duration - duration for which log should be captured, Default - P5D")
        parser.add_argument('--size_limit', default='500MB', dest='size_limit',
            help="Size Limit - Support Bundle size limit per node, Default - 500MB")
        parser.add_argument('--binlogs', type=UtilsSupportBundle.str2bool, default=False, dest='binlogs',
            help="Include/Exclude Binary Logs, Default = False")
        parser.add_argument('--coredumps', type=UtilsSupportBundle.str2bool, default=False, dest='coredumps',
            help="Include/Exclude Coredumps, Default = False")
        parser.add_argument('--stacktrace', type=UtilsSupportBundle.str2bool, default=False, dest='stacktrace',
            help="Include/Exclude stacktrace, Default = False")
        parser.add_argument('--modules', dest='modules',
            help="list of components & services to generate support bundle.")
        args=parser.parse_args()
        return args

    @staticmethod
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
    args = UtilsSupportBundle.parse_args()
    UtilsSupportBundle.generate(
        bundle_id=args.bundle_id,
        target_path=args.path,
        cluster_conf_url=args.cluster_conf,
        duration = args.duration,
        size_limit = args.size_limit,
        binlogs = args.binlogs,
        coredumps = args.coredumps,
        stacktrace = args.stacktrace
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)
