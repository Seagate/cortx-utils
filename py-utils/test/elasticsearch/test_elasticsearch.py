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

import unittest
import requests
from elasticsearch import Elasticsearch

from cortx.utils.validator.v_service import ServiceV


class ElasticsearchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.elasticsearch = Elasticsearch(host='localhost', port=9200)
        self.index = "elasticsearch_test"
        self.data = {
            "test": "elasticsearch_service"
            }

    def test_ES_connection(self):
        res = requests.get('http://localhost:9200')
        self.assertEqual(200, res.status_code)

    def test_service_running(self):
        ServiceV().validate('isrunning', ["elasticsearch"])

    def test_insert_data(self):
        # Insert data
        res = self.elasticsearch.index(index=self.index, id=1, body=self.data)
        self.assertEqual(res['result'], "created")
        self.elasticsearch.delete(index=self.index, id=1)

    def test_get_data(self):
        # Get data
        self.elasticsearch.index(index=self.index, id=1, body=self.data)
        res = self.elasticsearch.get(index=self.index, id=1)
        self.assertIs(res['found'], True)
        self.elasticsearch.delete(index=self.index, id=1)

    def delete_data(self):
        # Delete index
        self.elasticsearch.index(index=self.index, id=1, body=self.data)
        res = self.elasticsearch.delete(index=self.index)
        self.assertIs(res['acknowledged'], True)
