#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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


from datetime import datetime, timezone
from schematics.types import (StringType, DateTimeType, BooleanType)

from cortx.utils.data.access import BaseModel


class CortxUser(BaseModel):
    _id = "user_id"

    user_id = StringType()
    user_type = StringType()
    user_role = StringType()
    password_hash = StringType()
    email = StringType()
    alert_notification = BooleanType()
    updated_time = DateTimeType()
    created_time = DateTimeType()

    def update(self, new_values: dict):
        if 'password' in new_values:
            self.password_hash = 'dummyhash'
            new_values.pop('password')
        for key in new_values:
            setattr(self, key, new_values[key])

        self.updated_time = datetime.now(timezone.utc)
