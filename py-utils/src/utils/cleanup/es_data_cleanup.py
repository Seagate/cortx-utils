#!/usr/bin/python3

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

import errno
import json
import logging
import os
import traceback
from datetime import datetime, timedelta

import requests


class esCleanup:
    def __init__(self, service_name, path):
        self._path = path
        self.logger = self.get_logger(service_name, path)

    def remove_old_data_from_indexes(self, days, host, indexes, field):
        self.logger.debug('Will keep data from indexes for [%s] days', days)
        date_n_days_ago = datetime.now() - timedelta(days=days)
        date_dago = str(datetime.strftime(date_n_days_ago, '%Y.%m.%d'))
        self.logger.debug('Will remove all data from indexes earlier than [%s]', date_dago)
        headers = {'Content-type': 'application/json'}
        d = {"query": {"range": {f"{field}": {"lt": f"now-{days}d"}}}}
        for index in indexes:
            try:
                response = requests.post(
                    f'http://{host}/{index}/_delete_by_query', data=json.dumps(d), headers=headers)
            except Exception:
                msg = f'ERROR: cannot delete data for {index}: {traceback.format_exc()}'
                self.logger.error(msg)
            if response.status_code == 200:
                res = json.loads(response.text)
                msg = f'deleted {res.get("total",0)} old record from {index} resp: {response.text}'
                self.logger.info(msg)

    @staticmethod
    def get_logger(filename, path):
        """check/create directory for common logs."""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        # added hardcoded logger "util_log" to avoid duplicate log
        # in csm_cleanup.log
        logger = logging.getLogger("util_log")
        logger.setLevel(logging.INFO)
        format_var = '%(name)s %(levelname)s %(message)s'
        formatter = logging.Formatter(format_var)
        fh = logging.FileHandler(os.path.join(path, f"{filename}.log"))
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        return logger

    # Remove selected index from es db
    def remove_by_index(self, host, index):
        response = requests.delete(f'http://{host}/{index}')
        if response.status_code == 200:
            self.logger.debug('index %s removed successfully', index)
        else:
            msg = f'error removing index {index} :{response.status_code}'
            self.logger.error(msg)
        return response.status_code
