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

import errno
from urllib.parse import urlparse

from cortx.utils.conf_store import Conf
from cortx.utils.conf_store.error import ConfError


class DbConf:
    _cluster_index = 'dbconf-cluster'
    _db_index = 'dbconf'
    _consul_host = None
    _consul_port = None

    @classmethod
    def init(cls, cluster_conf):
        """Initiallize DbConf."""
        Conf.load(cls._cluster_index, cluster_conf, skip_reload=True)
        cls._get_consul_netloc()
        if cls._consul_host is None or cls._consul_port is None:
            raise ConfError(errno.ENOENT, f'Consul KV configuration not found in {cluster_conf}')
        Conf.load(cls._db_index, f"consul://{cls._consul_host}:{cls._consul_port}/utils_db_conf",
                  skip_reload=True)

    @classmethod
    def _get_consul_netloc(cls):
        """Get Consul KV netlocation."""
        eps = Conf.get(cls._cluster_index, f'cortx>external>consul>endpoints')
        for ep in eps:
            parsed_url = urlparse(ep)
            if parsed_url.scheme == 'http':
                cls._consul_host = parsed_url.hostname
                cls._consul_port = parsed_url.port
                break

    @classmethod
    def import_database_conf(cls, db_conf: str):
        """Import database configuration from the external ConfStore."""
        consul_login = Conf.get(cls._cluster_index, 'cortx>external>consul>admin')
        consul_secret = Conf.get(cls._cluster_index, 'cortx>external>consul>secret')

        import_index = 'dbconfsrc'
        Conf.load(import_index, db_conf)
        Conf.copy(import_index, cls._db_index)
        Conf.set(cls._db_index, 'databases>consul_db>config>hosts[0]', cls._consul_host)
        Conf.set(cls._db_index, 'databases>consul_db>config>port', cls._consul_port)
        Conf.set(cls._db_index, 'databases>consul_db>config>login', consul_login)
        Conf.set(cls._db_index, 'databases>consul_db>config>password', consul_secret)
        Conf.save(cls._db_index)

    @classmethod
    def export_database_conf(cls):
        """Export database configuration to the Python dict."""
        export_index = 'exportdbconf'
        Conf.load(export_index, 'dict:{"k":"v"}', fail_reload=False)
        Conf.copy(cls._db_index, export_index)
        db_config = {
            'databases': Conf.get(export_index,'databases'),
            'models': Conf.get(export_index, 'models')
        }
        db_config['databases']["consul_db"]["config"]["port"] = int(
            db_config['databases']["consul_db"]["config"]["port"])
        return db_config

