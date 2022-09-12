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
import pathlib
from datetime import datetime, timedelta
from cortx.utils.log import Log

from cortx.utils.support_framework.errors import BundleError


class FilterLog:
    """Provides Filter interfaces for support bundle."""

    @staticmethod
    def _get_delim_value(duration:str, delim:str) -> int:
        """
        Returns value for passed delim.

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
        Parses duration and and converts correspondign time in millisecons.

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
        Truncate the Log file's size to the required file size,.

        Returns the output file after writing in dest_dir.
        """
        with open(os.path.join(src_dir, file_name), 'r+b') as ReadHandle,\
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
    def limit_time(src_dir, dest_dir, duration, file_name_reg_ex,
        log_timestamp_regex = '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}',
        datetime_format = '%Y-%m-%d %H:%M:%S'):
        """
        Filters out log in the src_dir that were generated between passed.

        duration and copies them to dest_dir

        Args:
            src_dir [str]: source directory from where logs will be fetched
            dest_dir [str]: destination directory where logs will be dumped
            duration [str]: Duration in ISO 8601 format,
                            eg: 2020-09-06T05:30:00P5DT3H3S
            file_name_reg_ex [str]: File name regex
            log_timestamp_regex [str] : regex format for timestamp to be
                                        fetched from log file using re library
            datetime_format [str] : datetime format for regex

        Raises:
            BundleError: In case of failure

        Example:
            for log_timestamp 2022-07-10T05:45:36,
            datetime_format: '%Y-%m-%dT%H:%M:%S'
            log_timestamp_regex:
            '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}'
        """
        invalid_chars = re.findall("[^PTDHMS0-9-:]+", duration)
        if invalid_chars:
            raise BundleError(errno.EINVAL, "Invalid duration passed! "
            + f"unexpected characters: {invalid_chars}")

        include_lines_without_timestamp = False
        supported_file_types = ['.log', '.txt']
        start_time, end_time = FilterLog._parse_duration(duration)
        Log.info(f'start_time = {start_time}, end_time = {end_time}')
        # sort files based on timestamp
        list_of_files = filter(lambda f: os.path.isfile(
            os.path.join(src_dir, f)), os.listdir(src_dir))
        # sort the files based on last modification time in descending order
        list_of_files = sorted(list_of_files,
            key=lambda f: os.path.getmtime(os.path.join(src_dir, f)),
            reverse=True)
        for file in list_of_files:
            log_scope_exceeded = False
            log_written_to_file = False
            op_file = os.path.join(dest_dir, 'tmp_' + file)
            if file.startswith(file_name_reg_ex):
                in_file = os.path.join(src_dir, file)
                file_extension = pathlib.Path(file).suffix
                if file_extension not in supported_file_types:
                    FilterLog._collect_rotated_log_file(
                        in_file, dest_dir, start_time, end_time)
                    continue
                # TODO: Parse log lines using timestamp in more optimal way,
                # like using divide & conquer approach, to decide log lines
                # falling with in time range.
                with open(in_file, 'r') as fd_in, open(op_file, 'a') as fd_out:
                    line = fd_in.readline()
                    while (line):
                        regex_res = re.search(log_timestamp_regex, line)
                        log_duration = regex_res.group(0) if regex_res else None
                        if log_duration:
                            # convert log timestamp to datetime object
                            try:
                                log_time = datetime.strptime(log_duration, datetime_format)
                                if start_time <= log_time and log_time <= end_time:
                                    include_lines_without_timestamp = True
                                    log_written_to_file = True
                                    fd_out.write(line)
                                elif log_time > end_time and include_lines_without_timestamp:
                                    include_lines_without_timestamp = False
                                    log_scope_exceeded = True
                                    break
                            # There will be some log lines which lies under passed
                            # duration, but has no timestamp, those lines will
                            # throw ValueError while trying to fetch log
                            # timestamp, to capture such logs, we have set a
                            # flag include_lines_without_timestamp = True
                            except ValueError:
                                if include_lines_without_timestamp:
                                    log_written_to_file = True
                                    fd_out.write(line)
                        line = fd_in.readline()
                try:
                    if log_written_to_file:
                        final_op_file = os.path.join(dest_dir, file)
                        os.rename(op_file, final_op_file)
                    else:
                        os.remove(op_file)
                    if log_scope_exceeded:
                        break
                except OSError as e:
                    raise BundleError(errno.EINVAL, "Failed to filter log " +
                        f"file based on time duration. ERROR:{e}")

    @staticmethod
    def _collect_rotated_log_file(in_file: str, dest_dir: str,
            start_time: str, end_time: str):
        """Collect rotated log files(.gz) in support bundle if its
           creation time is in given time duration."""
        creation_time = os.path.getctime(in_file)
        # convert creation_time into datetime format e.g %Y-%m-%d %H:%M:%S.
        c_time = datetime.fromtimestamp(creation_time)
        if start_time <= c_time and c_time <= end_time:
            dest_file = os.path.join(dest_dir, os.path.basename(in_file))
            shutil.copyfile(in_file, dest_file)
