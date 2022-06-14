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

import errno
import time
import json
import re
import uuid
from enum import Enum

from cortx.template import Singleton
from cortx.utils.kv_store.kv_store import KvStoreFactory
from cortx.utils.kv_store import KvPayload
from cortx.utils.activity_tracker.error import ActivityError
from cortx.utils.activity_tracker import const

class Status(Enum):

    NEW = const.NEW
    IN_PROGRESS = const.IN_PROGRESS
    COMPLETED = const.COMPLETED
    FAILED = const.FAILED
    SUSPENDED = const.SUSPENDED

    @staticmethod
    def list() -> list:
        """Returns list of status values."""
        return list(map(lambda c: c.value, Status))

class ActivityEntry:
    """Represents System Activity"""

    def __init__(self, **kwargs):
        """Initializes the backend for the Activity Store."""
        self._payload = KvPayload()
        activity_id = kwargs.get(const.ID)
        if activity_id is None:
            activity_name = kwargs.get(const.NAME)
            resource_path = kwargs.get(const.RESOURCE_PATH)
            description = kwargs.get(const.DESCRIPTION)
            if activity_name is None or resource_path is None or description is None:
                raise ActivityError(errno.EINVAL, "Missing activity_name/resource_path/description")

            self._id = uuid.uuid1().hex
            self._payload[const.ID] = self._id
            self._payload[const.NAME] = activity_name
            self._payload[const.RESOURCE_PATH] = resource_path
            self._payload[const.DESCRIPTION] = description
            self._payload[const.PROGRESS] = 0
            self._payload[const.STATUS] = const.NEW
            self._payload[const.STATUS_DESC] = f"{const.CREATED_DESC}: {activity_name}"
            self._payload[const.CREATED_TIME] = int(time.time())
        else:
            self._id = activity_id
            for key, value in kwargs.items():
                self._payload[key] = value

    @property
    def id(self) -> str:
        return self._id

    @property
    def payload(self) -> dict:
        return self._payload

    def set_attr(self, attr: str, val: str):
        self._payload[attr] = val

    def set_status(self, progress: int, status: str, status_description: str):
        self._payload[const.PROGRESS] = progress
        self._payload[const.STATUS] = status
        self._payload[const.STATUS_DESC] = status_description
        self._payload[const.UPDATED_TIME] = int(time.time())

    def start(self):
        self._payload[const.UPDATED_TIME] = int(time.time())

    def finish(self, status: str = ""):
        self._payload[const.PROGRESS] = 100
        self._payload[const.UPDATED_TIME] = int(time.time())
        self._payload[const.STATUS] = status


class Activity(metaclass=Singleton):
    """Represent Activity Framework. Singleton Class"""
    _kv_store = None

    @staticmethod
    def init(backend_url):
        """Initializes the backend for the Activity Store."""
        Activity._kv_store = KvStoreFactory.get_instance(backend_url)

    @staticmethod
    def create(name:str, resource_path: str, description: str):
        """
        Creates an activity.

        Sets progress to 0 and status to NEW.
        Records the current time as the created time.
        """
        activity = ActivityEntry(name=name, resource_path=resource_path,
            description=description)
        Activity._kv_store.set([activity.id], [activity.payload.json])
        return activity

    @staticmethod
    def start(activity: ActivityEntry):
        """Start the activity. Records the current time as the start time."""
        if not isinstance(activity, ActivityEntry):
            raise ActivityError(errno.EINVAL, "start(): Invalid arg %s", activity)
        activity.start()
        Activity._kv_store.set([activity.id], [activity.payload.json])

    @staticmethod
    def finish(activity: ActivityEntry):
        """Completes a activity. Records current time as the completion time."""
        if not isinstance(activity, ActivityEntry):
            raise ActivityError(errno.EINVAL, "finish(): Invalid arg %s", activity)
        activity.finish()
        Activity._kv_store.set([activity.id], [activity.payload.json])

    @staticmethod
    def update(activity: ActivityEntry, progress: int, status: str, status_description: str):
        """
        Updates the activity progress, status and status_description.
        Records the current time as the updated time.
        """
        if not isinstance(activity, ActivityEntry):
            raise ActivityError(errno.EINVAL, "update(): Invalid arg %s", activity)
        try:
            status = Status(status).value
        except ValueError:
            raise ActivityError(errno.EINVAL, "update(): invalid status value %s", status)
        activity.set_status(progress, status, status_description)
        Activity._kv_store.set([activity.id], [activity.payload.json])

    @staticmethod
    def search(resource_path: str, filters: list) -> list:
        """Searches for a activity as per given criteria."""
        activity_list = Activity._kv_store.get_keys(resource_path)
        out_list = []
        for activity_id in activity_list:
            val = Activity._kv_store.get([activity_id])
            data = json.loads(val[0])
            matched = True
            for f in filters:
                key_spec = re.split("[^a-zA-Z_]", f)
                if key_spec[0] not in data.keys():
                    matched = False
                    break
                vars()[key_spec[0]] = data[key_spec[0]]
                _, r = [i.strip() for i in f.split("==")]
                r = r.replace("'","")
                if str(data[key_spec[0]]) != r:
                    matched = False
                    break
            if matched:
                out_list.append(activity_id)
        return out_list

    @staticmethod
    def get(activity_id: str):
        """Gets the activity details by activity_id."""
        val = Activity._kv_store.get([activity_id])
        if len(val) == 0 or val[0] is None:
            raise ActivityError(errno.EINVAL, "get(): invalid activity id %s", activity_id)
        data = json.loads(val[0])
        return ActivityEntry(**data)
