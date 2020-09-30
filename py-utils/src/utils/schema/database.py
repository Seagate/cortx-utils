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

DATABASE = {
    "databases": {
        "consul_db": {
            "import_path": "ConsulDB",
            "config": {
                "host": "localhost",
                "port": 8500,
                "login": "",
                "password": ""
            }
        },
        "es_db": {
            "import_path": "ElasticSearchDB",
            "config": {
                "host": "localhost",
                "port": 9200,
                "login": "",
                "password": "",
                "replication": 1
            }
        },
    },
    "models": [
        {
            "import_path": "cortx.utils.ha.dm.models.decisiondb.DecisionModel",
            "database": "consul_db",
            "config": {
                "consul_db": {
                    "collection": "HA"
                }
            }
        },
        {
            "import_path": "cortx.utils.product_features.model.UnsupportedFeaturesModel",
            "database": "es_db",
            "config": {
                "es_db": {
                    "collection": "config"
                }
            }
        }

    ]
}
