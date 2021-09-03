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

from setuptools import setup
import sys



# Get the version string from command line
version = "1.0.0"
for arg in sys.argv:
    if arg.startswith("--version") or arg.startswith("-v"):
        version = arg.split("=")[1]
        sys.argv.remove(arg)


setup(
    name="cortx-py-utils-test",
    version=version,
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
        "cortx.utils.test.schema",
        "cortx.utils.test.cli_framework",
        "cortx.utils.test.discovery",
        "cortx.utils.test.iem_framework",
        "cortx.utils.test.consul",
        "cortx.utils.test.discovery",
        "cortx.utils.test.discovery.solution",
        "cortx.utils.test.discovery.solution.lr2",
        "cortx.utils.test.discovery.solution.lr2.server",
        "cortx.utils.test.discovery.solution.lr2.storage",
        "cortx.utils.test.elasticsearch"
    ],
    package_data={
        "": [
            "*.json",
            "plans/*.pln",
            "schema/*.json",
            "kv_store/*.json",
            "conf_store/*.json",
            "message_bus/*.conf",
            "cli_framework/test_data/*.json",
            "iem_framework/*.json",
            "discovery/solution/lr2/*.json",
        ]
    },
    entry_points={
        'console_scripts': [
            'run_test = cortx.utils.test.run_test:tmain'
        ]
    }
)
