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

import os
import sys
from setuptools import setup


if not os.path.isfile("./VERSION"):
    print("error: VERSION file not found!", file=sys.stderr)
    sys.exit(1)

# Fetch version
with open("VERSION") as v_file:
    utils_version = v_file.read().strip()


setup(
    name="cortx-py-utils-test",
    version=utils_version,
    url="https://github.com/Seagate/cortx-utils/py-utils/test",
    license="Seagate",
    author="Seagate Foundation Team",
    description="Common Python utilities for CORTX",
    python_requires=">=3.6",
    install_requires=["cortx-py-utils"],
    package_dir={"cortx.utils.test": "."},
    packages=[
        "cortx.utils.test",
        "cortx.utils.test.plans",
        "cortx.utils.test.validator",
        "cortx.utils.test.kv_store",
        "cortx.utils.test.message_bus",
        "cortx.utils.test.conf_store",
        "cortx.utils.test.service_handler",
        "cortx.utils.test.ssh_connection",
        "cortx.utils.test.ha_dm",
        "cortx.utils.test.cli_framework",
        "cortx.utils.test.iem_framework",
        "cortx.utils.test.consul_service",
        "cortx.utils.test.discovery",
        "cortx.utils.test.discovery.solution",
        "cortx.utils.test.discovery.solution.lr2",
        "cortx.utils.test.discovery.solution.lr2.server",
        "cortx.utils.test.discovery.solution.lr2.storage",
        "cortx.utils.test.elastic_search",
        "cortx.utils.test.support_bundle",
        "cortx.utils.test.cmd_framework",
    ],
    package_data={
        "": [
            "VERSION",
            "plans/*.pln",
            "ha_dm/*.json",
            "ha_dm/test_schema/*.json",
            "kv_store/*.json",
            "conf_store/*.json",
            "conf_store/*.yaml",
            "message_bus/*.conf",
            "cli_framework/test_data/*",
            "iem_framework/*.json",
            "discovery/solution/lr2/*.json",
            "support_bundle/*.yaml",
        ]
    },
    entry_points={
        'console_scripts': [
            'run_test = cortx.utils.test.run_test:tmain'
        ]
    }
)
