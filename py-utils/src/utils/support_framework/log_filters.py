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

import os
import errno
import shutil

from cortx.utils.support_framework.errors import BundleError


class FilterLog:
    """Provides Filter interfaces for support bundle."""

    @staticmethod
    def _get_size_in_bytes(size: str):
        """Returns the size in bytes unit."""
        size_in_bytes = ''
        units = [('GB', 1024**3),
                ('MB', 1024**2),
                ('KB', 1024),
                ('B', 1)]
        for suffix, multiplier in units:
            if size.endswith(suffix):
                num_units = size[:-len(suffix)]
                size_in_bytes = float(num_units) * multiplier
                break
        return int(size_in_bytes)

    @staticmethod
    def _truncate_file_size(src_dir: str, dest_dir: str, file_name: str,
                           original_file_size: int, required_file_size: int):
        """
        Truncate the Log file's size to the required file size,

        Returns the output file after writing in dest_dir.
        """
        with open(os.path.join(src_dir, file_name), 'r+b') as ReadHandle, \
                open(os.path.join(dest_dir, file_name), 'w+b') as WriteHandle:
            ReadHandle.seek(original_file_size - required_file_size)
            WriteHandle.write(ReadHandle.read())
        try:
            os.truncate(os.path.join(dest_dir, file_name), required_file_size)
        except OSError as error:
            raise BundleError(errno.EINVAL, f"Failed to truncate the file, ERROR:{error}")

    @staticmethod
    def limit_size(src_dir: str, dest_dir: str, size: str, file_name_reg_ex: str):
        """Filter the log files in the source dir based on file size requested."""
        if not os.path.exists(src_dir):
            raise BundleError(errno.EINVAL, f"Source dir not present: {src_dir},"
                              "Please check for valid directory path.")

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        if file_name_reg_ex.endswith('*'):
            file_name_reg_ex = file_name_reg_ex[:-1]

        list_of_files = filter(lambda f: os.path.isfile(os.path.join(src_dir, f)),
                        os.listdir(src_dir))
        # sort the files based on last modification time in descending order
        list_of_files = sorted(list_of_files,
                        key = lambda f: os.path.getmtime(os.path.join(src_dir, f)),
                        reverse=True)
        required_file_size = FilterLog._get_size_in_bytes(size.upper())
        for file_name in list_of_files:
            if file_name.startswith(file_name_reg_ex):
                file_size = os.stat(os.path.join(src_dir, file_name)).st_size
                if file_size <= required_file_size:
                    shutil.copy(os.path.join(src_dir, file_name), dest_dir)
                    required_file_size = required_file_size - file_size
                else:
                    # Truncate the file from the beginning to match the required file size
                    FilterLog._truncate_file_size(src_dir, dest_dir, file_name,
                        file_size, required_file_size)
                    break

    @staticmethod
    def limit_time(src_dir, dest_dir, duration, file_name_reg_ex):
        # ToDo: Implementation of limit time filter.
        # currently making a copy of source file into the dest_dir.
        for file in os.listdir(src_dir):
            if file.startswith(file_name_reg_ex):
                shutil.copy(os.path.join(src_dir, file), dest_dir)
