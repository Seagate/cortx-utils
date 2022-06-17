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
from datetime import datetime, timezone
from schematics.types import (IntType, StringType, BooleanType, DateTimeType)

from cortx.utils.data.db.db_provider import (DataBaseProvider, GeneralConfig)
from cortx.utils.data.access.filters import Compare, And, Or
from cortx.utils.data.access import BaseModel, Query, SortOrder


class AlertModel(BaseModel):

    """
    Alert model example
    """

    _id = "alert_uuid"  # reference to another Alert model field to consider it as primary key
    alert_uuid = StringType()
    status = StringType()
    enclosure_id = IntType()
    module_name = StringType()
    description = StringType()
    health = StringType()
    health_recommendation = StringType()
    location = StringType()
    resolved = BooleanType()
    acknowledged = BooleanType()
    severity = StringType()
    state = StringType()
    extended_info = StringType()  # May be a Nested object
    module_type = StringType()
    updated_time = DateTimeType()
    created_time = DateTimeType()

    def to_primitive(self) -> dict:
        obj = super().to_primitive()

        if self.updated_time:
            obj["updated_time"] =\
                    int(self.updated_time.replace(tzinfo=timezone.utc).timestamp())
        if self.created_time:
            obj["created_time"] =\
                    int(self.created_time.replace(tzinfo=timezone.utc).timestamp())
        return obj

    def __hash__(self):
        return hash(self.alert_uuid)


ALERT1 = {'alert_uuid': 1,
          'status': "Success",
          'enclosure_id': 1,
          'module_name': "SSPL",
          'description': "Some Description",
          'health': "Good",
          'health_recommendation': "Replace Disk",
          'location': "USA",
          'resolved': True,
          'acknowledged': True,
          'severity': "Urgent",
          'state': "Unknown",
          'extended_info': "No",
          'module_type': "FAN",
          'updated_time': datetime.now(),
          'created_time': datetime.now()
          }

ALERT2 = {'alert_uuid': 2,
          'status': "Failed",
          'enclosure_id': 1,
          'module_name': "SSPL",
          'description': "Some Description",
          'health': "Good",
          'health_recommendation': "Replace Disk",
          'location': "India",
          'resolved': False,
          'acknowledged': False,
          'severity': "Neutral",
          'state': "Unknown",
          'extended_info': "No",
          'module_type': "FAN",
          'updated_time': datetime.now(),
          'created_time': datetime.now()
          }

ALERT3 = {'alert_uuid': 3,
          'status': "Failed",
          'enclosure_id': 1,
          'module_name': "SSPL",
          'description': "Some Description",
          'health': "Bad",
          'health_recommendation': "Replace Disk",
          'location': "Russia",
          'resolved': True,
          'acknowledged': True,
          'severity': "Normal",
          'state': "Unknown",
          'extended_info': "No",
          'module_type': "FAN",
          'updated_time': datetime.now(),
          'created_time': datetime.now()
          }

ALERT4 = {'alert_uuid': 4,
          'status': "Success",
          'enclosure_id': 1,
          'module_name': "SSPL",
          'description': "Some Description",
          'health': "Greate",
          'health_recommendation': "Replace Unity",
          'location': "Russia",
          'resolved': False,
          'acknowledged': False,
          'severity': "Neutral",
          'state': "Unknown",
          'extended_info': "No",
          'module_type': "FAN",
          'updated_time': datetime.now(),
          'created_time': datetime.now()
          }


async def example():
    conf = GeneralConfig({
        "databases": {
            "es_db": {
                "import_path": "ElasticSearchDB",
                "config": {
                    "hosts": ["localhost"],
                    "port": 9200,
                    "login": "",
                    "password": ""
                }
            }
        },
        "models": [
            {
                "import_path": "cortx.utils.data.db.examples.elasticsearch_storage.AlertModel",
                "database": "es_db",
                "config": {
                    "es_db":
                        {
                            "collection": "alert"
                        }
                }
            }]
    })

    db = DataBaseProvider(conf)

    alert1 = AlertModel(ALERT1)
    alert2 = AlertModel(ALERT2)
    alert3 = AlertModel(ALERT3)
    alert4 = AlertModel(ALERT4)

    await db(AlertModel).store(alert1)
    await db(AlertModel).store(alert2)
    await db(AlertModel).store(alert3)
    await db(AlertModel).store(alert4)

    res = await db(AlertModel).get(
        Query().filter_by(Compare(AlertModel.severity, "=", "Neutral")).order_by(
            AlertModel.severity,
            SortOrder.ASC))

    if res:
        for i, model in enumerate(res):
            print(f"Model {i}: {model.to_primitive()}")

    filter_condition = And(Compare(AlertModel.primary_key, "=", 1),
                 And(Compare(AlertModel.status, "=", "Success"),
                     Compare(AlertModel.primary_key, ">", 1)))

    query = Query().filter_by(filter_condition).order_by(AlertModel.primary_key, SortOrder.DESC)
    res = await db(AlertModel).get(query)
    print(f"Get by query: {[alert.to_primitive() for alert in res]}")

    to_update = {
        'location': "Russia",
        'alert_uuid': 22,
        'resolved': False,
        'created_time': datetime.now()
    }

    await db(AlertModel).update(filter_condition, to_update)

    res = await db(AlertModel).get(query)
    print(f"Get by query after update: {[alert.to_primitive() for alert in res]}")

    _id = 2
    res = await db(AlertModel).get_by_id(_id)
    if res is not None:
        print(f"Get by id = {_id}: {res.to_primitive()}")

    await db(AlertModel).update_by_id(_id, to_update)

    updated_id = to_update['alert_uuid']
    res = await db(AlertModel).get_by_id(updated_id)
    if res is not None:
        print(f"Get by id after update = {_id}: {res.to_primitive()}")

    filter_obj = Or(Compare(AlertModel.primary_key, "=", 1), Compare(AlertModel.primary_key, "=", 2),
                    Compare(AlertModel.primary_key, "=", 4))
    res = await db(AlertModel).count(filter_obj)
    print(f"Count by filter: {res}")

    res = await db(AlertModel).delete(filter_obj)
    print(f"Deleted by filter: {res}")

    _id = 3
    is_deleted = await db(AlertModel).delete_by_id(_id)
    print(f"Object by id = {_id} was deleted: {is_deleted}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(example())
    loop.close()
