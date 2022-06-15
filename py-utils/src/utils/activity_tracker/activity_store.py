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

from cortx.template import Singleton
from cortx.utils.kv_store.kv_store import KvStoreFactory
from cortx.utils.kv_store import KvPayload
from cortx.utils.activity_tracker.error import ActivityError
from cortx.utils.activity_tracker import const


class ActivityEntry:
    """Represents System Activity"""

    def __init__(self, **kwargs):
        """Initializes the backend for the Activity Store."""
        self._payload = KvPayload()
        activity_id = kwargs.get(const.ID)
        if activity_id is None:
            try:
                activity_name = kwargs[const.NAME]
                resource_path = kwargs[const.RESOURCE_PATH]
                description = kwargs[const.DESCRIPTION]
            except KeyError as e:
                raise ActivityError(errno.EINVAL, "Missing required key: %s", str(e))
            if activity_name is None or resource_path is None or description is None:
                raise ActivityError(errno.EINVAL, "Missing activity_name/resource_path/description")

            self._id = uuid.uuid1().hex
            self._payload[const.ID] = self._id
            self._payload[const.NAME] = activity_name
            self._payload[const.RESOURCE_PATH] = resource_path
            self._payload[const.DESCRIPTION] = description
            self._payload[const.PCT_PROGRESS] = 0
            self._payload[const.STATUS] = const.NEW
            self._payload[const.STATUS_DESC] = const.CREATED_DESC
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

    def set_progress(self, pct_progress: int, status_desc: str):
        if pct_progress < 0 or pct_progress > 99:
            raise ActivityError(errno.EINVAL, "update(): Invalid pct_progress: %s", pct_progress)
        self._payload[const.PCT_PROGRESS] = pct_progress
        self._payload[const.STATUS] = const.IN_PROGRESS
        self._payload[const.STATUS_DESC] = status_desc
        self._payload[const.UPDATED_TIME] = int(time.time())

    def finish(self, status_desc: str):
        self._payload[const.PCT_PROGRESS] = 100
        self._payload[const.STATUS] = const.COMPLETED
        self._payload[const.STATUS_DESC] = status_desc
        self._payload[const.UPDATED_TIME] = int(time.time())

    def suspend(self, status_desc: str):
        self._payload[const.STATUS] = const.SUSPENDED
        self._payload[const.STATUS_DESC] = status_desc
        self._payload[const.UPDATED_TIME] = int(time.time())


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

        Sets pct_progress to 0 and status to NEW.
        Records the current time as the created time.
        """
        activity = ActivityEntry(name=name, resource_path=resource_path,
            description=description)
        Activity._kv_store.set([activity.id], [activity.payload.json])
        return activity

    @staticmethod
    def update(activity: ActivityEntry, pct_progress: int, status_desc: str = const.IN_PROGRESS_DESC):
        """
        Updates the pct_progress and status_description.
        Sets the status to IN_PROGRESS.
        Records current time as the updated_time.
        """
        if not isinstance(activity, ActivityEntry):
            raise ActivityError(errno.EINVAL, "update(): Invalid arg %s", activity)
        activity_data = json.loads(activity.payload.json)
        if pct_progress < activity_data.get(const.PCT_PROGRESS):
            raise ActivityError(errno.EINVAL, "update(): pct_progress: %s\
                can not be less than the previously updated value", pct_progress)
        activity.set_progress(pct_progress, status_desc)
        Activity._kv_store.set([activity.id], [activity.payload.json])

    @staticmethod
    def finish(activity: ActivityEntry, status_desc: str = const.COMPLETED_DESC):
        """
        Completes the activity and updates the status_description.
        Sets the status to COMPLETE and pct_progress to 100.
        Records current time as the updated_time.
        """
        if not isinstance(activity, ActivityEntry):
            raise ActivityError(errno.EINVAL, "finish(): Invalid arg %s", activity)
        activity.finish(status_desc)
        Activity._kv_store.set([activity.id], [activity.payload.json])

    @staticmethod
    def suspend(activity: ActivityEntry, status_desc: str = const.SUSPENDED_DESC):
        """
        Suspends the activity and updates the status_description.
        Sets the status to SUSPEND.
        Records current time as the updated_time.
        """
        if not isinstance(activity, ActivityEntry):
            raise ActivityError(errno.EINVAL, "suspend(): Invalid arg %s", activity)
        activity.suspend(status_desc)
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
