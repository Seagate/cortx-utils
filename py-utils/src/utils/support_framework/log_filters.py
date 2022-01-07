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
import re
import errno
import shutil
from datetime import datetime, timedelta

from cortx.utils.support_framework.errors import BundleError

from cortx.utils.support_framework.errors import BundleError


class FilterLog:
    """Provides Filter interfaces for support bundle."""

    @staticmethod
    def _get_delim_value(duration:str, delim:str) -> int:
        """
        Returns value for passed delim

        Args:
            duration (str): duration is ISO 8601 format eg P4DT2H10M
            delim (str): duration delimiter (D/H/M/S)
        Returns:
            int: value for delimiter
        """
        if delim == 'P':
            match = re.search(f'[0-9T:\-]*{delim}', duration)
            return match.group(0)[:-1] if match else 0
        else:
            match = re.search(f'[0-9]+{delim}', duration)
            return int(match.group(0)[:-1]) if match else 0

    @staticmethod
    def _parse_duration(duration:str):
        """
        Parses duration and and converts correspondign time in millisecons

        Args:
            duration (str): Duraion in ISO 8601 format,
                            eg: 2020-09-06T05:30:00P5DT3H3S
                            where the first time stamp is the start time for
                            logs to be captured and D/H/M/S are duration ie
                            D: Days, H: Hours, M: Minutes, S: Seconds
        Returns:
            datetime, datetime: datetime obj of start_time and end_time for log
                                capture
        """
        start_time = FilterLog._get_delim_value(duration, 'P')
        # convert start_time string into datetime object if start_time is passed
        if start_time:
            start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')

        days = FilterLog._get_delim_value(duration, 'D')
        hours = FilterLog._get_delim_value(duration, 'H')
        minutes = FilterLog._get_delim_value(duration, 'M')
        seconds = FilterLog._get_delim_value(duration, 'S')

        duration_seconds = timedelta(days=days, hours=hours,  minutes=minutes,
            seconds=seconds).total_seconds()
        # if start time : end time = start time + duration
        # else end time = current_time ; start time = current_time - duration
        if start_time:
            end_time = datetime.fromtimestamp(
                start_time.timestamp() + duration_seconds)
        else:
            end_time = datetime.now()
            start_time = datetime.fromtimestamp(
                end_time.timestamp() - duration_seconds)
        return start_time, end_time

    @staticmethod
    def _is_valid_log_line(log_line, start_time, end_time):
        """
        checks if line passed is between start imte and end time

        Args:
            log_line (str): single log line
            start_time (datetime): datetime object of log start time
            end_time (datetime): datetime object of log end time

        Returns:
            [boot]: returns true if the log was added between start time and
                    end time else false
        """
        log_duration = log_line[:20].strip()
        if log_duration:
            # convert log timestamp to datetime object
            log_time = datetime.strptime(log_duration, '%Y-%m-%d %H:%M:%S')
        else:
            return False

        if start_time <= log_time and log_time <= end_time:
            return True
        else:
            return False


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
        """
        filters out log in the src_dir that were not generated between passed
        duration and copies them to dest_dir

        Args:
            src_dir [str]: source directory from where logs will be fetched
            dest_dir [str]: destination directory where logs will be dumped
            duration [str]: Duraion in ISO 8601 format,
                            eg: 2020-09-06T05:30:00P5DT3H3S
            file_name_reg_ex [str]: File name regex

        Raises:
            BundleError: In case of failure
        """
        invalid_chars = re.findall("[^PTDHMS0-9-:]+", duration)
        if invalid_chars:
            raise BundleError(errno.EINVAL,"Invalid duration passed! "
            + f"unexpected charecters: {invalid_chars}")

        start_time, end_time = FilterLog._parse_duration(duration)
        for file in os.listdir(src_dir):
            op_file = os.path.join(dest_dir, 'tmp_' + file)
            if file.startswith(file_name_reg_ex):
                with open(file, 'r') as fd_in, open(op_file, 'a') as fd_out:
                    line = fd_in.readline()
                    while(line):
                        if FilterLog._is_valid_log_line(line, start_time,
                            end_time):
                            fd_out.write(line)
                        line = fd_in.readline()
                try:
                    final_op_file = os.path.join(dest_dir, file)
                    os.rename(op_file, final_op_file)
                except OSError as e:
                    raise BundleError(errno.EINVAL, "Failed to filter log " +
                        f"file based on time duration. ERROR:{e}")
