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
import shutil
import tarfile
import errno

from cortx.utils.support_bundle.error import SupportBundleError


class SupportBundle:
    """ Generate support bundle for py-utils"""

    def __init__(self):
        self.path = "/tmp/cortx/support_bundle/"
        self.tar_name = "py-utils"
        self.tmp_src = "/tmp/cortx/py-utils/"
        self.files_to_bundle = {
            "message_bus": "/var/log/cortx/utils/message_bus/MessageBus.log",
            "iem_and_rest":
                "/var/log/cortx/utils/utils_server/utils_server.log",
            "kafka": "/var/log/cortx/utils/utils_setup.log",
            "kafka_server": "/opt/kafka/config/server.properties",
            "kafka_zookeeper": "/opt/kafka/config/zookeeper.properties"
        }

    def generate_support_bundle(self):
        """ Generate a tar file """
        for key, value in self.files_to_bundle.items():
            if os.path.exists(value):
                self.copy_file(value)
        self.generate_tar()
        self.clear_tmp_files()

    def copy_file(self, source: str, destination: str = None):
        """ Copy a file from source to destination location """
        directory = os.path.dirname(self.tmp_src)
        if not os.path.exists(directory):
            os.makedirs(directory)
        if destination is None:
            destination = self.tmp_src + os.path.basename(source)
        try:
            shutil.copy2(source, destination)
        except FileNotFoundError as fe:
            raise SupportBundleError(errno.EINVAL, "File not found %s", fe)

    def generate_tar(self):
        """ Generate tar.gz file at given path """
        tar_file_name = self.path + self.tar_name + ".tar.gz"
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        with tarfile.open(tar_file_name, "w:gz") as tar:
            tar.add(self.tmp_src, arcname=os.path.basename(self.tmp_src))

    def clear_tmp_files(self):
        """ Clean tmp files after support bundle generation completed """
        shutil.rmtree(self.tmp_src)
