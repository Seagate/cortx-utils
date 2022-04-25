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

from cortx.template import Singleton
from cortx.utils.task_framework.error import TaskError
from cortx.utils.kv_store.kv_store import KvStoreFactory
from cortx.utils.kv_store import KvPayload

class TaskEntry:
    """Represents System Activity."""

    def __init__(self, *args, **kwargs): 
        self._payload = KvPayload()
        task_id = kwargs.get('id')
        if task_id is None:
            resource_path = kwargs.get('resource_path')
            description = kwargs.get('description')
            if resource_path is None or description is None:
                raise TaskError(errno.EINVAL, "Missing resource_path/description")

            self._id = f'{resource_path}>%s' %time.time()
            self._payload['id'] = self._id
            self._payload['resource_path'] = resource_path
            self._payload['description'] = description
            self._payload['pct_complete'] = 0
        else:
            self._id = task_id
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

    def set_status(self, pct_complete: int, status: str):
        self._payload['pct_complete'] = pct_complete
        self._payload['status'] = status

    def start(self):
        self._payload['start_time'] = time.time()

    def finish(self, status: str = ""):
        self._payload['pct_complete'] = 100
        self._payload['finish_time'] = time.time()
        self._payload['status'] = status


class Task(metaclass=Singleton):
    """Represent Task Framework. Singleton Class."""
    _kv_store = None

    @staticmethod
    def init(backend_url):
        """Initializes the backend for the Task Store."""
        Task._kv_store = KvStoreFactory.get_instance(backend_url)

    @staticmethod
    def create(resource_path: str, description: str):
        """Creates a task for the given resource."""
        task = TaskEntry(resource_path=resource_path, description=description)
        Task._kv_store.set([task.id], [task.payload.json])
        return task

    @staticmethod
    def start(task: TaskEntry):
        """Start the task. Records the current time as the start time."""
        if not isinstance(task, TaskEntry):
            raise TaskError(errno.EINVAL, "start(): Invalid arg %s", task)
        task.start()
        Task._kv_store.set([task.id], [task.payload.json])

    @staticmethod
    def finish(task: TaskEntry):
        """Completes a task. Records current time as the completion time."""
        task.finish()
        Task._kv_store.set([task.id], [task.payload.json])

    @staticmethod
    def update(task: TaskEntry, pct_complete: int, status: str):
        """Updates the task progress."""
        task.set_status(pct_complete, status)
        Task._kv_store.set([task.id], [task.payload.json])

    @staticmethod
    def search(resource_path: str, filters: list) -> list:
        """Searches for a task as per given criteria."""
        task_list = Task._kv_store.get_keys(resource_path)
        out_list = []
        for task_id in task_list:
            val = Task._kv_store.get([task_id])
            data = json.loads(val[0])
            matched = True
            for f in filters:
                key_spec = re.split("[^a-zA-Z_]", f)
                if key_spec[0] not in data.keys():
                    matched = False
                    break
                vars()[key_spec[0]] = data[key_spec[0]]
                if not eval(f):
                    matched = False
                    break
            if matched:
                out_list.append(task_id)
        return out_list
                
    @staticmethod
    def get(task_id: str):
        """Gets the task details"""
        val = Task._kv_store.get([task_id])       
        if len(val) == 0 or val[0] is None: 
            raise TaskError(errno.EINVAL, "get(): invalid task id %s", task_id)
        data = json.loads(val[0])
        return TaskEntry(**data)
