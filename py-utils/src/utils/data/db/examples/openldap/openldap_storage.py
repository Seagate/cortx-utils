#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
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

import asyncio
from datetime import datetime
import os
import pathlib
import sys


def print_items(items):
    for item in items:
        print(item.to_primitive())


async def example():
    conf = GeneralConfig({
        "databases": {
            "openldap": {
                "import_path": "OpenLdap",
                "config": {
                    "hosts": ["127.0.0.1"],
                    "port": 389,
                    "login": "cn=sgiamadmin,dc=seagate,dc=com",
                    "password": "+_14zxKRJG=0ru"
                }
            }
        },
        "models": [
            {
                "import_path": "cortx.utils.data.db.examples.openldap.cortxuser_model.CortxUser",
                "database": "openldap",
                "config": {
                    "openldap": {
                        "collection": "ou=accounts,dc=csm,dc=seagate,dc=com"
                    }
                }
            }]
    })

    SAMPLE_USER = {
        "user_id": "eos22623demo",
        'user_type': 'csm',
        'email': 'eos22623demo@test.com',
        'password_hash': 'demopasswd',
        'user_role': 'manage',
        'created_time': datetime.now(),
        'updated_time': datetime.now(),
        'alert_notification': True
    }

    db = DataBaseProvider(conf)

    items = await db(CortxUser).get(Query())
    print('Collection status before addition')
    print_items(items)
    print(20 * '-')

    sample_user = CortxUser(SAMPLE_USER)
    await db(CortxUser).store(sample_user)

    print('Collection status after addition')
    updated_items = await db(CortxUser).get(Query())
    print_items(updated_items)
    print(20 * '-')


if __name__ == "__main__":
    py_utils_rel_path = os.path.join(os.path.dirname(pathlib.Path(__file__)), '../../../../../..')
    sys.path.insert(1, py_utils_rel_path)

    from cortx.utils.data.access import Query
    from cortx.utils.data.db.db_provider import (DataBaseProvider, GeneralConfig)
    from cortx.utils.data.db.examples.openldap.cortxuser_model import CortxUser

    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
    loop.close()
