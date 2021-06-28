#!/bin/python3

# CORTX Python common library.
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

import os.path
import random
import shutil
import tarfile
import errno

from cortx.utils.support_bundle.error import SupportBundleError
from cortx.utils.conf_store import Conf


class SupportBundle:
    """ Generate support bundle for py-utils"""
    _default_path = "/tmp/cortx/support_bundle/"
    _tar_name = "py-utils"
    _tmp_src = "/tmp/cortx/py-utils/"
    _files_to_bundle = {
        "message_bus": "/var/log/cortx/utils/message_bus/MessageBus.log",
        "iem_and_rest":
            "/var/log/cortx/utils/utils_server/utils_server.log",
        "utils_setup": "/var/log/cortx/utils/utils_setup.log",
        "kafka_server": "/opt/kafka/config/server.properties",
        "kafka_zookeeper": "/opt/kafka/config/zookeeper.properties"
    }

    @staticmethod
    def generate(target_path=None):
        """ Generate a tar file """
        for key, value in SupportBundle._files_to_bundle.items():
            if os.path.exists(value):
                SupportBundle.__copy_file(value)
        SupportBundle.__kafka_get_log_location_and_copy()
        SupportBundle.__generate_tar(target_path)
        SupportBundle.__clear_tmp_files()

    @staticmethod
    def __copy_file(source: str, destination: str = None):
        """ Copy a file from source to destination location """
        directory = os.path.dirname(SupportBundle._tmp_src)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if destination is None:
            destination = os.path.join(SupportBundle._tmp_src,
                os.path.basename(source))
        try:
            shutil.copy2(source, destination)
        except FileNotFoundError as fe:
            raise SupportBundleError(errno.EINVAL, "File not found %s", fe)

    @staticmethod
    def __generate_tar(target_path=None):
        """ Generate tar.gz file at given path """
        target_path = target_path if target_path is not None \
            else SupportBundle._default_path
        tar_file_name = os.path.join(target_path,
            SupportBundle._tar_name + ".tar.gz")
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        with tarfile.open(tar_file_name, "w:gz") as tar:
            tar.add(SupportBundle._tmp_src,
                arcname=os.path.basename(SupportBundle._tmp_src))

    @staticmethod
    def __kafka_get_log_location_and_copy():
        files_lst = SupportBundle._files_to_bundle
        # Same index will be used to test multiple times to init random
        r_num = str(int(random.random() * 10))
        if os.path.exists(files_lst["kafka_server"]) and os.path.exists(
                files_lst["kafka_zookeeper"]):
            to_be_collected = {}
            Conf.load('kafka_server'+r_num,
                "properties://" + files_lst["kafka_server"])
            Conf.load('kafka_zookeeper'+r_num,
                "properties://" + files_lst["kafka_zookeeper"])

            to_be_collected['kafka_log_dirs'] = Conf.get('kafka_server'+r_num,
                "log.dirs", "/tmp/kafka-logs")
            to_be_collected['zookeeper_data_log_dir'] = Conf.get(
                'kafka_zookeeper'+r_num, "dataLogDir")
            to_be_collected['zookeeper_data_dir'] = Conf.get(
                'kafka_zookeeper'+r_num, "dataDir", "/var/zookeeper")
            # Copy entire kafka and zookeeper logs
            for key, value in to_be_collected.items():
                if value and os.path.exists(value):
                    shutil.copytree(value, SupportBundle._tmp_src + key)

    @staticmethod
    def __clear_tmp_files():
        """ Clean tmp files after support bundle generation completed """
        shutil.rmtree(SupportBundle._tmp_src)
