#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
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

import os
import json

from cortx.utils.conf_store import Conf


class QueryConfData:
    """Query Data."""
    _query_idx = "query_idx"
    _data_idx = "data_idx"
    _local_file = '/tmp/local_conf.conf'
    _local_conf = "yaml://" + _local_file

    def __init__(self):
        _f = QueryConfData._local_file
        if os.path.exists(_f): os.remove(_f)

    def get_data(self, kv_url: str):
        """Get data related to the parent key from config."""
        return self._get_data(kv_url)

    def _get_data(self, kv_url: str):
        """Return data in dict format."""

        Conf.load(QueryConfData._query_idx, kv_url)
        _data_keys = Conf.get_keys(QueryConfData._query_idx)

        Conf.load(QueryConfData._data_idx, QueryConfData._local_conf)
        Conf.copy(QueryConfData._query_idx, QueryConfData._data_idx, _data_keys)
        Conf.save(QueryConfData._data_idx)

        from cortx.utils.conf_store import ConfStore
        _cs = ConfStore()
        _cs.load(QueryConfData._data_idx,  QueryConfData._local_conf)
        _data = _cs.get_data(QueryConfData._data_idx)
        print(_data)
        return _data.get_data()


class QueryDeployment:
    """ """
    _query_conf = None
    @staticmethod
    def init(**kwargs):
        """Static init for initialising and setting attributes."""
        if QueryDeployment._query_conf is None:
            QueryDeployment._query_conf = QueryConfData()

    @staticmethod
    def get_cortx_topology(kv_url: str) -> dict:
        """ """
        if QueryDeployment._query_conf is None:
            QueryDeployment.init()

        _data = {}
        _data = QueryDeployment._query_conf.get_data(kv_url)
        if not len(_data) > 0:
            raise(QueryCortxConfError, f"Invalid data in {kv_url}")

        return QueryDeployment._get_cortx_topology(_data)

    def _get_cortx_topology(data: dict) -> dict:
        """ """
        _config = {}
        with open('sample_topology.yaml') as f:
            _config = json.load(f)
        
        return dict(_config)

class QueryCortxConfError:
    pass
