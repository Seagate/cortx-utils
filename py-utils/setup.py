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
from fnmatch import fnmatch
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

# Get the list of all openldap template files
openldap_tmpl_files = glob.glob('src/utils/setup/openldap/templates/*.*')
# Get the list of ldif files
openldap_ldif_files = glob.glob('src/utils/setup/openldap/*.ldif')
# Get list of consul template file
consul_tmpl_files = glob.glob('src/utils/setup/consul/templates/*.*')

# Get the list of all elasticsearch template files
elasticsearch_tmpl_files = glob.glob(
    'src/utils/setup/elasticsearch/templates/*.*')

with open('LICENSE', 'r') as lf:
    license = lf.read()

with open('README.md', 'r') as rf:
    long_description = rf.read()

def get_install_requirements() -> list:
    with open('python_requirements.txt') as req:
        install_requires = [line.strip() for line in req]
    try:
        with open('python_requirements.ext.txt') as extreq:
            install_requires = install_requires + [line.strip() for line in extreq]
    except Exception:
        pass  ## log it!
    return install_requires

def get_requirements_files() -> list:
    req_file_list = [req_file for req_file in os.listdir(".") \
        if fnmatch(req_file, "python_requirements.*txt")]
    return req_file_list

setup(name='cortx-py-utils',
      version=utils_version,
      url='https://github.com/Seagate/cortx-utils/py-utils',
      license='Seagate',
      author='Alexander Voronov',
      author_email='alexander.voronov@seagate.com',
      description='Common Python utilities for CORTX',
      package_dir={'cortx': 'src'},
      packages=['cortx', 'cortx.utils',
                'cortx.template', 'cortx.support',
                'cortx.test_framework',
                'cortx.utils.amqp', 'cortx.utils.amqp.rabbitmq',
                'cortx.utils.cleanup', 'cortx.utils.data',
                'cortx.utils.data.access', 'cortx.utils.data.db',
                'cortx.utils.data.db.consul_db',
                'cortx.utils.data.db.elasticsearch_db',
                'cortx.utils.data.db.openldap',
                'cortx.utils.ha.hac',
                'cortx.utils.ha.dm', 'cortx.utils.ha.dm.models',
                'cortx.utils.ha.dm.repository', 'cortx.utils.ha',
                'cortx.utils.validator', 'cortx.utils.kv_store',
                'cortx.utils.conf_store', 'cortx.utils.message_bus',
                'cortx.utils.product_features', 'cortx.utils.security',
                'cortx.utils.schema', 'cortx.utils.appliance_info',
                'cortx.setup', 'cortx.support', 'cortx.utils.service',
                'cortx.utils.setup', 'cortx.utils.setup.kafka',
                'cortx.utils.cli_framework', 'cortx.utils.cmd_framework',
                'cortx.utils.utils_server', 'cortx.utils.iem_framework',
                'cortx.utils.discovery', 'cortx.utils.common',
                'cortx.utils.support_framework',
                'cortx.utils.manifest', 'cortx.utils.setup.openldap',
                'cortx.utils.setup.consul', 'cortx.utils.setup.elasticsearch',
                'cortx.utils.audit_log', 'cortx.utils.cortx',
                'cortx.utils.rgwadmin',
                ],
      package_data={
        'cortx': ['py.typed'],
      },
      entry_points={
        'console_scripts': [
            'hac = cortx.utils.ha.hac.hac:main',
            'conf = cortx.utils.conf_store.conf_cli:main',
            'utils_setup = cortx.setup.utils_setup:main',
            'iem = cortx.utils.iem_framework.iem_cli:main',
            'kafka_setup = cortx.utils.setup.kafka.kafka_setup:main',
            'utils_support_bundle = cortx.support.utils_support_bundle:main',
            'cortx_support_bundle = cortx.support.cortx_support_bundle:main',
            'openldap_setup = cortx.utils.setup.openldap.openldap_setup:main',
            'consul_setup = cortx.utils.setup.consul.consul_setup:main',
            'elasticsearch_setup = cortx.utils.setup.elasticsearch.elasticsearch_setup:main'
        ]
      },
      data_files = [ ('/var/lib/cortx/ha/specs', specs),
                     ('/opt/seagate/cortx/utils/conf', tmpl_files),
                     ('/opt/seagate/cortx/utils/conf', get_requirements_files()),
                     ('/var/lib/cortx/ha', ['src/utils/ha/hac/args.yaml',
                                            'src/utils/ha/hac/re_build.sh']),
                     ('%s/conf' % utils_path, ['src/setup/setup.yaml',
                                 'cortx.conf.sample', 'VERSION',
                                 'src/support/support.yaml',
                                 'src/utils/support_framework/support_bundle.yaml',
                                 'src/utils/support_framework/0-support_bundle.conf']),
                     ('%s/conf' % utils_path, tmpl_files),
                     ('%s/conf' % utils_path, openldap_tmpl_files),
                     (f'{utils_path}/conf', consul_tmpl_files),
                     ('%s/conf' % utils_path, openldap_ldif_files),
                     ('%s/conf' % utils_path, [
                     'src/utils/setup/openldap/openldapsetup_prereqs.json',
                     'src/utils/setup/openldap/openldap_prov_config.yaml',
                     'src/utils/setup/openldap/config/openldap_config.yaml.sample',
                     'src/utils/setup/consul/consul_setup.yaml',
                     'src/utils/setup/openldap/config/openldap_config_unsafe_attributes.yaml']),
                     (f'{utils_path}/conf/elasticsearch', elasticsearch_tmpl_files),
                     (f'{utils_path}/conf/elasticsearch', [
                        'src/utils/setup/elasticsearch/config/elasticsearch.yml.sample',
                        'src/utils/setup/elasticsearch/setup.yaml']),
                     ('/etc/systemd/system', ['src/utils/message_bus/'
                                              'cortx_message_bus.service'])],
      long_description=long_description,
      zip_safe=False,
      python_requires='>=3.6',
      install_requires=get_install_requirements())
