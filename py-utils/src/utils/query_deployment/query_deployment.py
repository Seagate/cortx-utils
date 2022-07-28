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

from cortx.utils.conf_store import Conf

class Topology:
    topology = {
                "cortx": {
                  "common": {
                    "release": {
                      "name": "CORTX",
                      "version": "2.0.0-5072"
                    }
                  }
                },
                "cluster": [
                  {
                    "id": "0007ec45379e36d9fa089a3d615c32a3",
                    "name": "cortx-cluster",
                    "security": {
                      "device_certificate": "/etc/cortx/solution/ssl/stx.pem",
                      "domain_certificate": "/etc/cortx/solution/ssl/stx.pem",
                      "ssl_certificate": "/opt/seagate/cortx/s3/install/haproxy/ssl/s3.seagate.com.pem"
                    },
                    "storage_set": [
                      {
                        "name": "storage-set-1",
                        "durability": {
                          "dix": {
                            "data": "1",
                            "parity": "0",
                            "spare": "0"
                          },
                          "sns": {
                            "data": "1",
                            "parity": "0",
                            "spare": "0"
                          }
                        }
                      }
                    ]
                  }
                ],
                "nodes": [
                    {"machine_id":"c4a32f1a4a3a43c1c65563511d9536b0",
                    "cluster_id": "0007ec45379e36d9fa089a3d615c32a3",
                    "hostname": "data1-node2",
                    "name": "data1-node2",
                    "node_id": "cortx-data-g1-2.cortx-data-headless.cortx.svc.cluster.local",
                    "storage_set": "storage-set-1",
                    "type": "data_node/1",
                    "version": "2.0.0-84",
                    "components": [
                      {
                        "name": "utils",
                        "version": "2.0.0-5058"
                      },
                      {
                        "name": "motr",
                        "version": "2.0.0-5060",
                        "services": [
                          "io"
                        ]
                      },
                      {
                        "name": "hare",
                        "version": "2.0.0-5072"
                      }
                    ],
                    "cvg": [
                      {
                        "devices": {
                          "data": [
                            "/dev/sdc",
                            "/dev/sdd"
                          ],
                          "metadata": [
                            "/dev/sdb"
                          ],
                          "log": [
                            "/dev/sdh"
                          ]
                        },
                        "name": "cvg-01",
                        "type": "ios"
                      }
                    ]
                  }
                ]
        }


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
            raise QueryDeploymentError(errno.EINVAL, f"Invalid data in {kv_url}")

        return QueryDeployment._get_cortx_topology(_data)

    def _get_cortx_topology(data: dict) -> dict:
        """ """
        _config = {}
        _config = Topology.topology
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
