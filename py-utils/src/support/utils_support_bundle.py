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
    _files_to_bundle = {
        'message_bus': '/var/log/cortx/utils/message_bus/message_bus.log',
        'utils_server':
            '/var/log/cortx/utils/utils_server/utils_server.log',
        'utils_setup': '/var/log/cortx/utils/utils_setup.log',
        'kafka_server': '/opt/kafka/config/server.properties',
        'kafka_zookeeper': '/opt/kafka/config/zookeeper.properties'
    }

    @staticmethod
    def generate(bundle_id: str, target_path: str):
        """ Generate a tar file """
        if os.path.exists(UtilsSupportBundle._tmp_src):
            UtilsSupportBundle.__clear_tmp_files()
        for value in UtilsSupportBundle._files_to_bundle.values():
            if os.path.exists(value):
                UtilsSupportBundle.__copy_file(value)
        UtilsSupportBundle.__collect_kafka_logs()
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
        target_path = target_path if target_path is not None \
            else UtilsSupportBundle._default_path
        tar_name = bundle_id if bundle_id else UtilsSupportBundle._tar_name
        tar_file_name = os.path.join(target_path, tar_name + '.tar.gz')
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        with tarfile.open(tar_file_name, 'w:gz') as tar:
            tar.add(UtilsSupportBundle._tmp_src,
                arcname=os.path.basename(UtilsSupportBundle._tmp_src))

    @staticmethod
    def __collect_kafka_logs():
        files_lst = UtilsSupportBundle._files_to_bundle
        if os.path.exists(files_lst['kafka_server']) and os.path.exists(
                files_lst['kafka_zookeeper']):
            to_be_collected = {}
            Conf.load('kafka_server',
                'properties://' + files_lst['kafka_server'], fail_reload=False)
            Conf.load('kafka_zookeeper',
                'properties://' + files_lst['kafka_zookeeper'],
                fail_reload=False)

            to_be_collected['kafka_log_dirs'] = Conf.get('kafka_server',
                'log.dirs', '/tmp/kafka-logs')
            to_be_collected['zookeeper_data_log_dir'] = Conf.get(
                'kafka_zookeeper', 'dataLogDir')
            to_be_collected['zookeeper_data_dir'] = Conf.get(
                'kafka_zookeeper', 'dataDir', '/var/zookeeper')
            # Copy entire kafka and zookeeper logs
            for key, value in to_be_collected.items():
                if value and os.path.exists(value):
                    shutil.copytree(value,
                        os.path.join(UtilsSupportBundle._tmp_src, key))
        # Collect systemctl status of kafka and kafka-zookeeper
        _cli = {'kafka_systemctl_status': "systemctl status kafka",
                'zookeeper_systemctl_status':
                "systemctl status kafka-zookeeper"}
        file_name = 'kafka_zookeeper_status.yaml'
        path = f'yaml://{os.path.join(UtilsSupportBundle._tmp_src, file_name)}'
        if not os.path.exists(UtilsSupportBundle._tmp_src):
            os.makedirs(UtilsSupportBundle._tmp_src, exist_ok=True)
        Conf.load('kafka_and_zookeeper_status', path)
        for key, cmd in _cli.items():
            cmd_proc = SimpleProcess(cmd)
            result_data = cmd_proc.run()
            err_msg = str(result_data[1], 'utf-8')
            result = err_msg if err_msg else str(result_data[0], 'utf-8')
            Conf.set('kafka_and_zookeeper_status', key, result)
        Conf.save('kafka_and_zookeeper_status')

    @staticmethod
    def __clear_tmp_files():
        """ Clean temporary files created by the support bundle """
        shutil.rmtree(UtilsSupportBundle._tmp_src)

    @staticmethod
    def parse_args():
        """
        Parse and return available argument

        Parameters:
        action: used to create| delete| status| cancel the support bundle
                script.
        bundle_id: Unique bundle id.
        path: Path where the generated support bundle tar file should
              be stored.
        modules: (Optional parameter) list the number of submodules
                 that need to be bundled. By Default all the modules
                 in the components will be bundled.
        """
        parser = argparse.ArgumentParser(description='''Bundle utils logs ''')
        parser.add_argument('action', help="Action can be create| status|"\
            + "delete| cancel")
        parser.add_argument('bundle_id', help='Unique bundle id')
        parser.add_argument('path', help='Path where the generated support'\
            +'bundle tar file should be stored', nargs='?',
            default="/var/seagate/cortx/support_bundle/")
        parser.add_argument('--modules', help="(Optional parameter) list the"\
            +"number of submodules that need to be bundled. By Default all"\
            +"the modules in the components will be bundled.")
        args=parser.parse_args()
        return args


def main():
    args = UtilsSupportBundle.parse_args()
    if args.action == 'create':
        UtilsSupportBundle.generate(bundle_id=args.bundle_id, target_path=args.path)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)
