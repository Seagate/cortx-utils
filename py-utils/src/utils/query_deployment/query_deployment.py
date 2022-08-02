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
import errno
from collections import defaultdict
from cortx.utils.conf_store import Conf

class Topology:
    topology = {
           "cortx": {
            "common": {
               "release": {}
                }
             },
            "cluster": [],
            "nodes": [],
            }
class QueryConfData:
    """Query Data."""
    _query_idx = "query_idx"
    _data_idx = "data_idx"
    _local_file = "/tmp/local_conf.conf"
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
        for key in Conf.get_keys(QueryConfData._data_idx):
            if 'num_'in key:
                Conf.delete(QueryConfData._data_idx, key)
        Conf.save(QueryConfData._data_idx)

        from cortx.utils.conf_store import ConfStore
        _cs = ConfStore()
        _cs.load(QueryConfData._data_idx,  QueryConfData._local_conf)
        _data = _cs.get_data(QueryConfData._data_idx)
        return _data.get_data()


class QueryDeployment:
    """ Query Deployment """
    _query_conf = None
    @staticmethod
    def init(**kwargs):
        """ Static init for initialising and setting attributes."""
        if QueryDeployment._query_conf is None:
            QueryDeployment._query_conf = QueryConfData()

    @staticmethod
    def get_cortx_topology(kv_url: str) -> dict:
        """ get cluster toplogy """
        if QueryDeployment._query_conf is None:
            QueryDeployment.init()

        _data = {}
        _data = QueryDeployment._query_conf.get_data(kv_url)
        if not len(_data) > 0:
            raise QueryDeploymentError(errno.EINVAL, f"Invalid data in {kv_url}")
        return QueryDeployment._get_cortx_topology(_data)

    def _get_cortx_topology(data: dict) -> dict:
        """ Map gconf fields to topology """
        nd = lambda: defaultdict(nd)
        _config = Topology.topology
        # to fetch cortx info
        _config["cortx"]["common"]["release"] = data["cortx"]["common"]["release"]
        
        # to fetch cluster_info
        for cluster_key, cluster_val in data['cluster'].items():
            cluster_info = nd()
            storage_set_info = nd()
            storage_set_list=[]
            cluster_info['security'] = data['cortx']['common']['security']
            if cluster_key == 'storage_set':
                for storage_info in data['cluster']['storage_set']:
                    for storage_key,storage_val in storage_info.items():
                        if storage_key != 'nodes':
                            storage_set_info[storage_key] = storage_val
                storage_set_list.append(storage_set_info)
                cluster_info['storage_set'] = storage_set_list
            else:
                cluster_info[cluster_key] = cluster_val
        _config['cluster'].append((json.dumps(cluster_info)))

        # to fetch Nodes Info
        for nodes_key in data['node'].keys():
            nodes_info = nd()
            nodes_info['machine_id'] = nodes_key
            for key, val in data['node'][nodes_key].items():
                if key =='provisioning':
                    # TODO: uncomment below once deployment time is supported by provisioner
                    # nodes_info['deployment_time'] = data['node'][nodes_key]['provisioning']['time']
                    nodes_info['version'] = data['node'][nodes_key]['provisioning']['version']
                else:
                    nodes_info[key] = val
                #TBD json dumps to dict
            _config["nodes"].append(json.dumps(nodes_info))
        return _config

class QueryDeploymentError(Exception):
    """Generic Exception with error code and output."""

    def __init__(self, rc, message, *args):
        """Initialize self."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Return str(self)."""
        if self._rc == 0: return self._desc
        return "error(%d): %s" % (self._rc, self._desc)
