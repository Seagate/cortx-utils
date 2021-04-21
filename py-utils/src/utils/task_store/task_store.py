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

from cortx.utils.task_store.error import TaskError
from cortx.utils.kv_store.kv_store import KvStoreFactory
from cortx.utils.kv_store import KvPayload


class TaskEntry:
    """ Represents System Activity """

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
        self._payload['{self._id}>pct_complete'] = pct_complete
        self._payload['{self._id}>status'] = status

    def start(self):
        self._payload['{self._id}>start_time'] = time.time()

    def finish(self, status: str = ""):
        self._payload['{self._id}>pct_complete'] = 100
        self._payload['f{self._id}>finish_time'] = time.time()
        self._payload['{self._id}>status'] = status


class Task:
    _kv_store = None

    @staticmethod
    def init(backend_url):
        Task._kv_store = KvStoreFactory.get_instance(backend_url)

    @staticmethod
    def create(resource_path: str, description: str):
        task = TaskEntry(resource_path=resource_path, description=description)
        Task._kv_store.set([task.id], [task.payload.get_data('json')])
        return task

    @staticmethod
    def start(task: TaskEntry):
        task.start()
        Task._kv_store.set([task.id], [task.payload.get_data('json')])

    @staticmethod
    def finish(task: TaskEntry):
        task.finish()
        Task._kv_store.set([task.id], [task.payload.get_data('json')])

    @staticmethod
    def update(task: TaskEntry, pct_complete: int, status: str):
        task.set_status(pct_complete, status)
        Task._kv_store.set([task.id], [task.payload.get_data('json')])

    @staticmethod
    def list(resource_path: str):
        return Task._kv_store.get_keys(resource_path)

    @staticmethod
    def get(task_id: str):
        val = Task._kv_store.get([task_id])       
        if val is None: 
            return val
        data = json.loads(val[0])
        return TaskEntry(**data)
