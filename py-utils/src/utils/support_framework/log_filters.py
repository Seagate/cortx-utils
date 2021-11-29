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
import shutil


class FilterLog:
    """Provides Filter interfaces for support bundle."""

    @staticmethod
    def limit_size(src_dir, dest_dir, size, file_name_reg_ex):
        # ToDo: Implementation of limit size filter.
        # currently making a copy of source file into the dest_dir.
        for file in os.listdir(src_dir):
            if file.startswith(file_name_reg_ex):
                shutil.copy(os.path.join(src_dir, file), dest_dir)


    @staticmethod
    def limit_time(src_dir, dest_dir, duration, file_name_reg_ex):
        # ToDo: Implementation of limit time filter.
        # currently making a copy of source file into the dest_dir.
        for file in os.listdir(src_dir):
            if file.startswith(file_name_reg_ex):
                shutil.copy(os.path.join(src_dir, file), dest_dir)
