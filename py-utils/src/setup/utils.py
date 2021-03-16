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

import errno
import json
import time

from cortx.utils.process import SimpleProcess


def _get_kafka_server_list(conf_url):
    """ Reads the ConfStore and derives keys related to message bus """

    from cortx.utils.conf_store import Conf
    Conf.load("cluster_config", conf_url)
    # Read the required keys
    all_servers = list((Conf.get("cluster_config", \
                        'cluster>server_nodes')).items())
    no_servers = len(all_servers)
    kafka_server_list = []
    kafka_servers = 0
    for i in range(no_servers):
        if 'kafka_server' in (Conf.get("cluster_config", \
                              f'cluster>{all_servers[i][1]}>roles')):
            kafka_server_list.append(Conf.get("cluster_config", \
                     f'cluster>{all_servers[i][1]}>network>mgmt>public_ip'))
            kafka_servers += 1
    if kafka_servers == 0 or kafka_server_list == None:
         raise ValueError("Data incorrect")
    return kafka_server_list


def _create_msg_bus_config(kafka_server_list):
    """ Create the config file required for message bus """

    from cortx.utils.conf_store import Conf
    with open(r'/etc/cortx/message_bus.conf.new', 'w+') as file:
        json.dump({}, file, indent=2)
    Conf.load("index", "json:///etc/cortx/message_bus.conf.new")
    Conf.set('index', 'message_broker>type', "kafka")
    for i in range(len(kafka_server_list)):
        Conf.set('index', f'message_broker>cluster[{i}]', \
                     {"server": kafka_server_list[i], "port": "9092"})
    Conf.save('index')
    # copy this conf file as message_bus.conf
    cmd = "/bin/mv /etc/cortx/message_bus.conf.new" + \
          " /etc/cortx/message_bus.conf"
    try:
        cmd_proc = SimpleProcess(cmd)
        res_op, res_err, res_rc = cmd_proc.run()
        if res_rc != 0:
            raise SetupError(errno.EIO, \
                       "/etc/cortx/message_bus.conf file creation failed, \
                        rc = %d", res_rc)
    except Exception as e:
        raise SetupError(errno.EIO, \
                  "/etc/cortx/message_bus.conf file creation failed, %s", e)
    return res_rc


class SetupError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        if self._rc == 0: return self._desc
        return "error(%d): %s" %(self._rc, self._desc)




class Utils:
    """ Represents Utils and Performs setup related actions """

    @staticmethod
    def validate(phase: str):
        """ Perform validtions """

        # Perform RPM validations
        pass

    @staticmethod
    def post_install():
        """ Performs post install operations """

        # Do the python packages installation
        cmd = "/bin/pip3 install -r " \
              + "/opt/seagate/cortx/utils/conf/requirements.txt"
        try:
            cmd_proc = SimpleProcess(cmd)
            res_op, res_err, res_rc = cmd_proc.run()
            if res_rc != 0:
                raise SetupError(errno.ENOENT, \
                                 "Python Package installation failed, rc=%d", \
                                 res_rc)
        except Exception as e:
            raise SetupError(errno.ENOENT, \
                             "Python Package installation failed, %s", e)
        return res_rc

    @staticmethod
    def init():
        """ Perform initialization """
        return 0

    @staticmethod
    def config(conf_url):
        """ Performs configurations """

        # Message Bus Config
        kafka_server_list = _get_kafka_server_list(conf_url)
        rc = _create_msg_bus_config(kafka_server_list)
        return rc

    @staticmethod
    def test():
        """ Perform configuration testing """
        from cortx.utils.setup.utils import MessageBusTest
        msg_test = MessageBusTest()
        # Send a message
        msg_test.send_msg(["Test Message"])
        # Recieve the same & validate
        msg = msg_test.receive_msg()
        if str(msg.decode("utf-8")) != "Test Message":
            raise SetupError(errno.EINVAL, "Unable to test the config")
        return 0

    @staticmethod
    def reset():
        """ Performs Configuraiton reset """
        return 0
