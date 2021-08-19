#!/bin/env python3

# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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

import requests
from elasticsearch import Elasticsearch, ElasticsearchException

from cortx.utils.conf_store import Conf
from cortx.utils.log import Log


class ElasticsearchTest:
    test_index = "test_index"

    def __init__(self, config, plan):
        Conf.load(self.test_index, config)

        Log.init(
            'ElasticsearchProvisioning',
            '/var/log/cortx/utils/elasticsearch', level='DEBUG')
        if plan:
            self.test_elasticsearch()

    def test_elasticsearch(self):
        """ create index, insert data, delete data """
        index = "elasticsearch_test"
        data = {
            "test": "elasticsearch_service"
            }
        # make sure ES is up and running
        machine_id = Conf.machine_id
        node_name = Conf.get(
            self.test_index, f'server_node>{machine_id}>name')
        try:
            res = requests.get(f'http://{node_name}:9200')
        except requests.RequestException as e:
            Log.error("Elasticsearch is not running. %s" % e)
            raise e

        try:
            es = Elasticsearch(host=node_name, port=9200)

            # Create index
            es.indices.create(index=index, ignore=400)

            # Insert data
            res = es.index(index=index, id=1, body=data)
            if res['result'] == "created":
                Log.info("Inserted data into %s, data - %s" % (index, res))

            # Get data
            res = es.get(index=index, id=1)
            if res['found']:
                Log.info("Found data into %s, data - %s" % (index, res))

            # Delete index
            res = es.indices.delete(index=index)
            if res['acknowledged']:
                Log.info("Deleted elasticsearch %s index." % index)

        except ElasticsearchException as e:
            Log.error("Exception in test %s" % e)
            raise e
