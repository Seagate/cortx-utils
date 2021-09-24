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

    SAMPLE_USER2 = {
        "user_id": "test1",
        'user_type': 'csm',
        'email': 'test1@test.com',
        'password_hash': '987dfsg231sdg234GG',
        'user_role': 'manage',
        'created_time': datetime.strptime("20210801045500Z", '%Y%m%d%H%M%SZ'),
        'updated_time': datetime.now(),
        'alert_notification': True
    }

    SAMPLE_USER3 = {
        "user_id": "test2",
        'user_type': 'csm',
        'email': 'test2@test.com',
        'password_hash': '12358ZHGJDhhasdfG',
        'user_role': 'manage',
        'created_time': datetime.strptime("20200103125530Z", '%Y%m%d%H%M%SZ'),
        'updated_time': datetime.now(),
        'alert_notification': True
    }

    SAMPLE_USER4 = {
        "user_id": "s3sampleuser",
        'user_type': 's3',
        'email': 's3sampleuser@s3.com',
        'password_hash': 'asghuoanmnxcbg',
        'user_role': 'monitor',
        'created_time': datetime.strptime("20210803120030Z", '%Y%m%d%H%M%SZ'),
        'updated_time': datetime.now(),
        'alert_notification': False
    }

    sample_users = [SAMPLE_USER, SAMPLE_USER2, SAMPLE_USER3, SAMPLE_USER4]

    db = DataBaseProvider(conf)

    items = await db(CortxUser).get(Query())
    print('Users collection')
    print_items(items)
    print(20 * '-')

    for user in sample_users:
        user_obj = CortxUser(user)
        await db(CortxUser).store(user_obj)

    print('Collection status after addition')
    updated_items = await db(CortxUser).get(Query())
    print_items(updated_items)
    print(20 * '-')

    print('Query search')
    filter_obj = And(
        Or(
            Compare(CortxUser.user_role, '=', 'manage'),
            Compare(CortxUser.user_role, "=", "admin")),
        Compare(CortxUser.user_type, '=', 'csm')
    )
    query = Query().filter_by(filter_obj).order_by(CortxUser.user_id, SortOrder.DESC)
    queried_items = await db(CortxUser).get(query)
    print_items(queried_items)
    print(20 * '-')

    print('Query generalized')
    filter_obj = And(
        Compare(CortxUser.created_time, '>=', datetime.strptime('20210827000005Z', '%Y%m%d%H%M%SZ')),
        Compare(CortxUser.alert_notification, '=', True)
    )
    query = Query().filter_by(filter_obj)
    queried_items = await db(CortxUser).get(query)
    print_items(queried_items)
    print(20 * '-')

    filter_obj = Compare(CortxUser.user_type, '=', 's3')
    to_update = {
        'user_role': 'admin'
    }
    num = await db(CortxUser).update(filter_obj, to_update)
    items = await db(CortxUser).get(Query())
    print(f'Updated - {num}')
    print_items(items)
    print(20 * '-')

    filter_obj = Or(
        Compare(CortxUser.user_type, '=', 's3'),
        Compare(CortxUser.user_id, 'like', 'est'))
    cnt = await db(CortxUser).count(filter_obj)
    print(f'Counted - {cnt}')
    print(20 * '-')

    num = await db(CortxUser).delete(None)
    items = await db(CortxUser).get(Query())
    print(f'Deleted - {num}')
    print_items(items)
    print(20 * '-')


if __name__ == "__main__":
    py_utils_rel_path = os.path.join(os.path.dirname(pathlib.Path(__file__)), '../../../../../..')
    sys.path.insert(1, py_utils_rel_path)

    from cortx.utils.data.access import Query, And, Or, Compare, SortOrder
    from cortx.utils.data.db.db_provider import (DataBaseProvider, GeneralConfig)
    from cortx.utils.data.db.examples.openldap.cortxuser_model import CortxUser

    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
    loop.close()
