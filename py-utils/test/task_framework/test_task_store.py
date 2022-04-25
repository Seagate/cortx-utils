#!/usr/bin/env python3

# # CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
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

import resource
import unittest
import os
import json

from cortx.utils.task_framework import Task

dir_path = os.path.dirname(os.path.realpath(__file__))
sample_file = os.path.join(dir_path, 'sample_tasks.json')
sample_file_url = f"json://{sample_file}"

def delete_file(file=sample_file):
    """Deletes temporary files."""
    try:
        if os.path.exists(file):
            os.remove(file)
    except OSError as e:
        print(e)

def load_data(file=sample_file):
    """Returns JSON object of the data in JSON file."""
    data = None
    try:
        with open(file,) as f_obj:
            data = json.load(f_obj)
    except FileNotFoundError as e:
        print(e)
    return data

class TestTaskStore(unittest.TestCase):
    """Test Task Store."""

    def test_task_store_create_task(self):
        """Test task creation."""
        Task.init(sample_file_url)
        task = Task.create("Tasks", "Task Status")
        rc = 0
        try:
            task_id = task.id.split('>')[1]
        except AttributeError as exc:
            print(exc)
            rc = 1
        self.assertEqual(rc, 0)
        try:
            tasks = load_data(sample_file)['Tasks']
            task_data = json.loads(tasks.get(task_id))
        except Exception as e:
            rc = 1
            print(e)
        self.assertEqual(rc, 0)
        self.assertEqual(task_data.get('resource_path'), "Tasks")
        self.assertEqual(task_data.get('description'), "Task Status")

    def test_task_store_start_task(self):
        """Test starting a task"""
        Task.init(sample_file_url)
        task = Task.create("Tasks", "Task Status")
        rc = 0
        try:
            task_id = task.id.split('>')[1]
        except AttributeError as exc:
            print(exc)
            rc = 1
        self.assertEqual(rc, 0)
        Task.start(task)
        try:
            tasks = load_data(sample_file)['Tasks']
            task_data = json.loads(tasks.get(task_id))
        except Exception as e:
            rc = 1
            print(e)
        self.assertEqual(rc, 0)
        self.assertIsNotNone(task_data.get('start_time'), "Start time key is not present")
            
    def test_task_store_update_task(self):
        """Test Update Task."""
        Task.init(sample_file_url)
        task = Task.create("Tasks", "Task Status")
        rc = 0
        try:
            task_id = task.id.split('>')[1]
        except AttributeError as exc:
            print(exc)
            rc = 1
        self.assertEqual(rc, 0)
        Task.start(task)
        pct_complete = 30
        task_status = "InProgress"
        Task.update(task, pct_complete, task_status)
        try:
            tasks = load_data(sample_file)['Tasks']
            task_data = json.loads(tasks.get(task_id))
        except Exception as e:
            rc = 1
            print(e)
        self.assertEqual(rc, 0)
        self.assertEqual(task_data.get('pct_complete'), pct_complete)
        self.assertEqual(task_data.get('status'), task_status)

    def test_task_store_get_task(self):
        """Test get task details."""
        Task.init(sample_file_url)
        task = Task.create("Tasks", "Task Status")
        task_details = Task.get(task.id)
        task_data = json.loads(task_details.payload.json)
        self.assertEqual(task_data.get('resource_path'), 'Tasks')
        self.assertEqual(task_data.get('description'), 'Task Status')
        
    def test_task_store_finish_task(self):
        """Test Finish task."""
        Task.init(sample_file_url)
        task = Task.create("Tasks", "Task Status")
        rc = 0
        try:
            task_id = task.id.split('>')[1]
        except AttributeError as exc:
            print(exc)
            rc = 1
        self.assertEqual(rc, 0)
        Task.start(task)
        Task.finish(task)
        try:
            tasks = load_data(sample_file)['Tasks']
            task_data = json.loads(tasks.get(task_id))
        except Exception as e:
            rc = 1
            print(e)
        self.assertIsNotNone(task_data.get('finish_time'), "finish_time key is not present")

    def test_task_store_search_task(self):
        """Test Search task."""
        Task.init(sample_file_url)
        task1 = Task.create("Tasks", "Task Status One")
        Task.start(task1)
        task2 = Task.create("Tasks", "Task Status Two")
        Task.start(task2)
        pct_complete = 30
        task_status = "InProgress"
        Task.update(task2, pct_complete, task_status)
        self.assertEqual(Task.search('Tasks', [f"pct_complete=={pct_complete}"])[0], task2.id)

    @classmethod
    def tearDownClass(cls):
        """Cleans up the resources created during prerequisite setup."""
        delete_file(sample_file)

if __name__ == '__main__':
    unittest.main()
