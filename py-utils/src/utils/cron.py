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

import datetime
from crontab import CronTab
from cortx.utils.log import Log


class CronJob:
    """Class to Schedule Cron Jobs."""

    def __init__(self, user):
        try:
            self._cron = CronTab(user=user)
        except OSError as e:
            Log.error(f"Cron User Error : {e}")
            self._cron = None

    def create_run_time(self, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        """
        Create Running time for Cron Jobs
        :return: Extended time from Current Time.
        """
        return datetime.datetime.now() + datetime.timedelta(days, seconds, microseconds, milliseconds, minutes, hours,
                                                            weeks)

    def create_new_job(self, command, comment, schedule_time):
        """
        Creeate new Cron jobs
        :param command: Command to be Executed in Cron job.
        :param comment: Comment for Cron Job.
        :param schedule_time: time at which cron should be executed.
        :return: None
        """
        if not self._cron:
            Log.error("Cron Job Object is not Instantiated")
            return
        Log.debug(f"Creating cron job for comment {comment}")
        _job = self._cron.new(command=command, comment=comment)
        _job.setall(schedule_time)
        self._cron.write()

    def remove_job(self, comment):
        """
        Remove Running/Scheduled Cron Jobs.
        :param comment: Comment for Cron Job. :type: String
        :return: None
        """
        if not self._cron:
            Log.error("Cron Job Object is not Instantiated")
            return
        Log.debug(f"Removing cron job for comment {comment}")
        cron_jobs = self._cron.find_comment(comment)
        for each_job in cron_jobs:
            self._cron.remove(each_job)
            self._cron.write()
