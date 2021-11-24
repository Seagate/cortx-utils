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

class FilterSupportBundle:
    """Provides Filter interfaces for support bundle."""

    @staticmethod
    def limit_size(src_dir, file_name_reg_ex, size, dest_dir):
        msg = "limit_size filter is not implemented yet"
        return msg

    @staticmethod
    def limit_time(start_time_and_duration, src_dir, file_name_reg_ex, dest_dir):
        msg = "limit_time filter is not implemented yet"
        return msg
