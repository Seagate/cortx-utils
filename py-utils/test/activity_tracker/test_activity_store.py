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

import unittest
import os
import json
import errno
from cortx.utils.activity_tracker.activity_store import Activity
from cortx.utils.activity_tracker.error import ActivityError

dir_path = os.path.dirname(os.path.realpath(__file__))
sample_file = os.path.join(dir_path, 'sample_activities.json')
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

class TestActivityStore(unittest.TestCase):
    """Test Activity Store."""

    def test_activity_store_create_activity(self):
        """Test activity creation."""
        Activity.init(sample_file_url)
        activity = Activity.create("Activity", "Activities", "Activity Status")
        rc = 0
        try:
            activity_id = activity.id
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity ID")
        self.assertEqual(rc, 0)
        with self.assertRaises(ActivityError):
            Activity.create("Activity", "Activities", None)
        try:
            activities = load_data(sample_file)
            activity_data = json.loads(activities.get(activity_id))
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity data")
        self.assertEqual(rc, 0)
        self.assertEqual(activity_data.get('resource_path'), "Activities")
        self.assertNotEqual(activity_data.get('resource_path'),"")
        self.assertEqual(activity_data.get('description'), "Activity Status")
        self.assertNotEqual(activity_data.get('description'),"")
        self.assertEqual(activity_data.get('pct_progress'), 0)
        self.assertEqual(activity_data.get('status'), "NEW")

    def test_activity_store_update_activity(self):
        """Test Update Activity."""
        Activity.init(sample_file_url)
        activity = Activity.create("Activity", "Activities", "Activity Status")
        rc = 0
        try:
            activity_id = activity.id
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity ID")
        self.assertEqual(rc, 0)
        pct_progress = 30
        status_desc = "Activity is in progress."
        Activity.update(activity, pct_progress, status_desc)
        try:
            activities = load_data(sample_file)
            activity_data = json.loads(activities.get(activity_id))
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity data")
        self.assertEqual(rc, 0)
        self.assertEqual(activity_data.get('pct_progress'), pct_progress)
        self.assertIsNotNone(activity_data.get('pct_progress'), "pct_progress key is not present")
        self.assertEqual(activity_data.get('status'), "IN_PROGRESS")
        self.assertIsNotNone(activity_data.get('status'), "status key is not present")
        self.assertEqual(activity_data.get('status_description'), status_desc)
        self.assertIsNotNone(activity_data.get('status_description'), "status_description key is not present")

    def test_activity_store_get_activity(self):
        """Test get activity details."""
        Activity.init(sample_file_url)
        activity = Activity.create("Activity", "Activities", "Activity Status")
        activity_details = Activity.get(activity.id)
        activity_data = json.loads(activity_details.payload.json)
        self.assertEqual(activity_data.get('name'), 'Activity')
        self.assertEqual(activity_data.get('resource_path'), 'Activities')
        self.assertEqual(activity_data.get('description'), 'Activity Status')

    def test_activity_store_finish_activity(self):
        """Test Finish activity."""
        Activity.init(sample_file_url)
        activity = Activity.create("Activity", "Activities", "Activity Status")
        activity1 = "activity"
        rc = 0
        try:
            activity_id = activity.id
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity ID")
        self.assertEqual(rc, 0)
        Activity.finish(activity, 0, "activity completed successfully.")
        with self.assertRaises(ActivityError):
            Activity.finish(activity1, 0)
        try:
            activities = load_data(sample_file)
            activity_data = json.loads(activities.get(activity_id))
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity data")
        self.assertIsNotNone(activity_data.get('updated_time'), "updated_time key is not present")
        self.assertEqual(activity_data.get('pct_progress'), 100)
        self.assertEqual(activity_data.get('rc'), 0)
        self.assertNotEqual(activity_data.get('rc'),"0")
        self.assertEqual(activity_data.get('status'), "COMPLETED")

    def test_activity_store_suspend_activity(self):
        """Test Finish activity."""
        Activity.init(sample_file_url)
        activity = Activity.create("Activity", "Activities", "Activity Status")
        activity1 = "activity"
        rc = 0
        try:
            activity_id = activity.id
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity ID")
        self.assertEqual(rc, 0)
        pct_progress = 40
        Activity.update(activity, pct_progress)
        Activity.suspend(activity, "activity suspended ..")
        with self.assertRaises(ActivityError):
            Activity.finish(activity1, 0)
        try:
            activities = load_data(sample_file)
            activity_data = json.loads(activities.get(activity_id))
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity data")
        self.assertIsNotNone(activity_data.get('updated_time'), "updated_time key is not present")
        self.assertEqual(activity_data.get('pct_progress'), pct_progress)
        self.assertEqual(activity_data.get('status'), "SUSPENDED")

    def test_activity_store_update_after_finish(self):
        """Test Finish activity."""
        Activity.init(sample_file_url)
        activity = Activity.create("Activity", "Activities", "Activity Status")
        rc = 0
        try:
            activity_id = activity.id
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity ID")
        self.assertEqual(rc, 0)
        pct_progress = 40
        Activity.update(activity, pct_progress)
        Activity.finish(activity, 0, "activity completed successfully")
        with self.assertRaises(ActivityError):
            pct_progress= 50
            Activity.update(activity, pct_progress)
        try:
            activities = load_data(sample_file)
            activity_data = json.loads(activities.get(activity_id))
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity data")
        self.assertEqual(activity_data.get('pct_progress'), 100)
        self.assertEqual(activity_data.get('status'), "COMPLETED")

    def test_activity_store_suspend_after_finish(self):
        """Test Finish activity."""
        Activity.init(sample_file_url)
        activity = Activity.create("Activity", "Activities", "Activity Status")
        rc = 0
        try:
            activity_id = activity.id
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity ID")
        self.assertEqual(rc, 0)
        pct_progress = 40
        Activity.update(activity, pct_progress)
        Activity.finish(activity, 0, "activity completed successfully")
        with self.assertRaises(ActivityError):
            pct_progress= 50
            Activity.suspend(activity)
        try:
            activities = load_data(sample_file)
            activity_data = json.loads(activities.get(activity_id))
        except:
            rc = 1
            raise ActivityError(errno.EINVAL, "Error: While fetching Activity data")
        self.assertEqual(activity_data.get('pct_progress'), 100)
        self.assertEqual(activity_data.get('status'), "COMPLETED")

    # Disabling the test as search functionality needs to be redesigned.
    # ToDo: Modify below test case once search functionality is available.
    # def test_activity_store_search_activity(self):
    #     """Test Search activity."""
    #     Activity.init(sample_file_url)
    #     activity1 = Activity.create("Activity", "Activities", "Activity Status One")
    #     Activity.start(activity1)
    #     activity2 = Activity.create("Activity","Activities", "Activity Status Two")
    #     Activity.start(activity2)
    #     pct_progress = 30
    #     status = "IN_PROGRESS"
    #     status_desc = "Activity is in progress."
    #     Activity.update(activity2, pct_progress, status, status_desc)
    #     self.assertEqual(Activity.search('Activities', [f"pct_progress=={pct_progress}"])[0], activity2.id)
    #     self.assertEqual(Activity.search('Activities', [f"status=='{status}'"])[0], activity2.id)
    #     self.assertEqual(Activity.search('Activities', ["status_description=='Activity Status Two'"])[0], activity2.id)

    @classmethod
    def tearDownClass(cls):
        """Cleans up the resources created during prerequisite setup."""
        delete_file(sample_file)

if __name__ == '__main__':
    unittest.main()
