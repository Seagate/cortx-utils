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

from cortx.utils.common import CortxConf
from cortx.utils.conf_store import Conf
from cortx.utils.errors import UtilsError
from cortx.utils.process import SimpleProcess


class SupportBundleError(UtilsError):
    """ SupportBundleError exception with error code and output """

    def __init__(self, rc, message, *args):
        super().__init__(rc, message, *args)


class UtilsSupportBundle:
    """ Generate support bundle for py-utils """
    _default_path = '/tmp/cortx/support_bundle/'
    _tar_name = 'py-utils'
    _tmp_src = '/tmp/cortx/py-utils/'
    LOG_DIR='/var/log'
    utils_log_dir = os.path.join(LOG_DIR, 'cortx/utils')
    _log_files_to_bundle = {
        'message_bus': 'message_bus/message_bus.log',
        'utils_server': 'utils_server/utils_server.log',
        'iem': 'iem/iem.log',
        'utils_setup': 'utils_setup.log'
    }
    _conf_files_to_bundle ={
        'cortx_conf': 'conf/cortx.conf',
        'message_bus_conf': 'conf/message_bus.conf',
        'iem_conf': 'conf/iem.conf'
    }

    @staticmethod
    def generate(bundle_id: str, target_path: str, cluster_conf: str):
        """ Generate a tar file """
        # Find log dirs
        CortxConf.init(cluster_conf=cluster_conf)
        log_base = CortxConf.get_storage_path('log')
        local_base = CortxConf.get_storage_path('local')
        machine_id = Conf.machine_id

        if os.path.exists(UtilsSupportBundle._tmp_src):
            UtilsSupportBundle.__clear_tmp_files()
        else:
            os.makedirs(UtilsSupportBundle._tmp_src)
        # Copy log files
        for log in UtilsSupportBundle._log_files_to_bundle.values():
            log_path = os.path.join(log_base,f'utils/{machine_id}', log)
            if os.path.exists(log_path):
                UtilsSupportBundle.__copy_file(log_path)
        # Copy configuration files
        shutil.copytree(os.path.join(local_base, 'utils/conf'),\
            os.path.join(UtilsSupportBundle._tmp_src, 'conf'))
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
            help="Cluster config file path for Support Bundle",\
            default="yaml:///etc/cortx/cluster.conf")
        parser.add_argument('-s', '--services', dest='services', nargs='+',\
            default='', help='List of services for Support Bundle')
        args=parser.parse_args()
        return args


def main():
    args = UtilsSupportBundle.parse_args()
    UtilsSupportBundle.generate(
        bundle_id=args.bundle_id,
        target_path=args.path,
        cluster_conf=args.cluster_conf
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)
