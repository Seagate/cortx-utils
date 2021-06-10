# CORTX-Py-Utils: CORTX Python common library.
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

import os
import glob
from setuptools import setup
import json
import sys

if not os.path.isfile("./cortx.conf.sample"):
    print("error: cortx.conf.sample file not found!", file=sys.stderr)
    sys.exit(1)

with open("cortx.conf.sample") as conf_file:
    build_data = json.load(conf_file)

# Fetch install_path
install_path = build_data["install_path"]
utils_path = "%s/cortx/utils" % install_path

if not os.path.isfile("./VERSION"):
    print("error: VERSION file not found!", file=sys.stderr)
    sys.exit(1)

# Fetch version
with open("VERSION") as v_file:
    utils_version = v_file.read().strip()

# Fetch ha spec file list
SPEC_DIR = "src/utils/ha/hac/specs/"
_ROOT = os.path.abspath(os.path.dirname(__file__)) + "/" + SPEC_DIR
specs = []
for root, directories, filenames in os.walk(_ROOT):
    for filename in filenames:
        specs.append(SPEC_DIR + filename)

# Get the list of template files
tmpl_files = glob.glob('src/setup/templates/*.*')

with open('LICENSE', 'r') as lf:
    license = lf.read()

with open('README.md', 'r') as rf:
    long_description = rf.read()

def get_install_requirements() -> list:
    install_requires = []
    with open('requirements.txt') as r:
        install_requires = [line.strip() for line in r]
    return install_requires


setup(name='cortx-py-utils',
      version=utils_version,
      url='https://github.com/Seagate/cortx-utils/py-utils',
      license='Seagate',
      author='Alexander Voronov',
      author_email='alexander.voronov@seagate.com',
      description='Common Python utilities for CORTX',
      package_dir={'cortx': 'src'},
      packages=['cortx', 'cortx.utils',
                'cortx.template',
                'cortx.utils.amqp', 'cortx.utils.amqp.rabbitmq',
                'cortx.utils.cleanup', 'cortx.utils.data',
                'cortx.utils.data.access', 'cortx.utils.data.db',
                'cortx.utils.data.db.consul_db',
                'cortx.utils.data.db.elasticsearch_db', 'cortx.utils.ha.hac',
                'cortx.utils.ha.dm', 'cortx.utils.ha.dm.models',
                'cortx.utils.ha.dm.repository', 'cortx.utils.ha',
                'cortx.utils.validator', 'cortx.utils.kv_store',
                'cortx.utils.conf_store', 'cortx.utils.message_bus',
                'cortx.utils.product_features', 'cortx.utils.security',
                'cortx.utils.schema', 'cortx.utils.appliance_info',
                'cortx.setup', 'cortx.utils.service',
                'cortx.utils.setup', 'cortx.utils.setup.kafka',
                'cortx.utils.cli_framework',
                'cortx.utils.rest_server', 'cortx.utils.iem_framework',
                'cortx.utils.support_bundle'
                ],
      package_data={
        'cortx': ['py.typed'],
      },
      entry_points={
        'console_scripts': [
            'hac = cortx.utils.ha.hac.hac:main',
            'conf = cortx.utils.conf_store.conf_cli:main',
            'utils_setup = cortx.setup.utils_setup:main',
            'kafka_setup = cortx.utils.setup.kafka.kafka_setup:main'
        ]
      },
      data_files = [ ('/var/lib/cortx/ha/specs', specs),
                     ('/var/lib/cortx/ha', ['src/utils/ha/hac/args.yaml',
                                            'src/utils/ha/hac/re_build.sh']),
                     ('%s/conf' % utils_path, ['requirements.txt', 'src/setup/setup.yaml',
                                 'cortx.conf.sample', 'VERSION',
                                 'src/utils/support_bundle/setup_path.yaml']),
                     ('%s/conf' % utils_path, tmpl_files),
                     ('/etc/systemd/system', ['src/utils/message_bus/'
                                              'cortx_message_bus.service'])],
      long_description=long_description,
      zip_safe=False,
      python_requires='>=3.6',
      install_requires=get_install_requirements())
