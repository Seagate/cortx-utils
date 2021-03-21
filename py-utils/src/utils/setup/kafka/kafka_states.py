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

from typing import List
from jinja2 import Environment, PackageLoader
import re
import os
from pathlib import Path


# TODO backup if needed
# TODO idempotence
# TODO test on in a real env
# TODO compare the resuls with provisioner's
#      salt state.apply components.misc_pkgs.kafka.config

MODULE_DIR = Path(__file__).resolve().parent

ZOOKEPER_PROPERTIES_PATH_TMPL = (
    "/opt/kafka/kafka_{kafka_version}/config/zookeeper.properties"
)
KAFKA_SERVER_PROPERTIES_PATH_TMPL = (
    "/opt/kafka/kafka_{kafka_version}/config/server.properties"
)
ZOOKEPER_MYID_PATH = Path('/var/lib/zookeeper/myid')

KAFKA_LOG_DIR = '/var/log/kafka'

# TODO remove once dummy testing is done
#      Note. these redefinitions might be used for local testing without
#            machines env setup
# ZOOKEPER_PROPERTIES_PATH_TMPL = (
#     "zookeeper/kafka_{kafka_version}_zookeeper.properties"
# )
# KAFKA_SERVER_PROPERTIES_PATH_TMPL = (
#     "zookeeper/kafka_{kafka_version}_server.properties"
# )
# ZOOKEPER_MYID_PATH = Path('zookeeper/test/myid')


def set_zookeeper_properties(kafka_version: str, servers: List[str]):
    """
    Sets Kafka zookeeper properties

    :param kafka_version: version of Kafka installed
    :param servers: list of server hostnames
    :return:
    """

    env = Environment(
        loader=PackageLoader('cortx.utils.setup.kafka', 'files')
    )
    template = env.get_template('zookeeper.properties.tmpl')
    rendered_zookeeper = template.render(servers=servers)
    Path(
        ZOOKEPER_PROPERTIES_PATH_TMPL.format(kafka_version=kafka_version)
    ).write_text(rendered_zookeeper)


def set_zookeeper_myid(server_id: str):
    """
    Sets zookeeper myid

    :param server_id: index of the current server
    :return:
    """

    zookeeper_id_file = ZOOKEPER_MYID_PATH
    zookeeper_id_file.parent.mkdir(exist_ok=True, parents=True)
    zookeeper_id_file.write_text(server_id)


def set_server_properties(kafka_version, servers, server_id):
    """
    Sets Kafka server properties

    :param kafka_version: version of Kafka installed
    :param servers: list of server hostnames
    :param server_id: index of the current server
    :return:
    """

    replacements = {
        re.compile('^broker.id=.*', re.MULTILINE): f"broker.id={server_id}",
        re.compile('^log.dirs=.*', re.MULTILINE): f"log.dirs={KAFKA_LOG_DIR}",
        re.compile(
            '^zookeeper.connect=.*', re.MULTILINE
        ): f"zookeeper.connect={','.join(servers)}"
    }

    server_properties_path = Path(
        KAFKA_SERVER_PROPERTIES_PATH_TMPL.format(kafka_version=kafka_version)
    )

    adds = []
    properties = None
    if server_properties_path.exists():
        properties = server_properties_path.read_text()
        for regex, repl in replacements.items():
            if regex.search(properties):
                properties = regex.sub(repl, properties)
            else:
                adds.append(repl)
    else:
        adds = list(replacements.values())

    if adds:
        if properties:
            adds.insert(0, properties)
        # [''] is to add a newline before EOF
        properties = os.linesep.join(adds + [''])

    server_properties_path.write_text(properties)
