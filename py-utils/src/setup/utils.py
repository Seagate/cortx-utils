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
from cortx.utils.validator.v_confkeys import ConfKeysV
from cortx.utils.validator.v_service import ServiceV

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
    def _create_msg_bus_config(kafka_server_list, port_list):
        """ Create the config file required for message bus """

        from cortx.utils.conf_store import Conf
        with open(r'/etc/cortx/message_bus.conf.new', 'w+') as file:
            json.dump({}, file, indent=2)
        Conf.load("index", "json:///etc/cortx/message_bus.conf.new")
        Conf.set("index", "message_broker>type", "kafka")
        for i in range(len(kafka_server_list)):
            Conf.set("index", f"message_broker>cluster[{i}]", \
                     {"server": kafka_server_list[i], "port": port_list[i]})
        Conf.save("index")
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

    @staticmethod
    def _get_kafka_server_list(conf_url):
        """ Reads the ConfStore and derives keys related to message bus """

        from cortx.utils.conf_store import Conf
        Conf.load("cluster_config", conf_url)

        keylist = ["cortx>software>common>message_bus_type",
                   "cortx>software>kafka>servers"]
        ConfKeysV().validate("exists", "cluster_config", keylist)

        msg_bus_type = Conf.get("cluster_config", \
                                "cortx>software>common>message_bus_type")
        if msg_bus_type != "kafka":
            raise SetupError(errno.EINVAL, \
                             "Message Bus do not support type %s" % msg_bus_type)
        # Read the required keys
        all_servers = Conf.get("cluster_config", \
                               "cortx>software>kafka>servers")
        no_servers = len(all_servers)
        kafka_server_list = []
        port_list = []
        for i in range(no_servers):
            # check if port is mentioned
            rc = all_servers[i].find(':')
            if rc == -1:
                port_list.append("9092")
                kafka_server_list.append(all_servers[i])
            else:
                port_list.append(all_servers[i][rc + 1:])
                kafka_server_list.append(all_servers[i][:rc])
        if len(kafka_server_list) == 0:
            raise SetupError(errno.EINVAL, \
                             "No valid Kafka server info provided for Config Key \
                             'cortx>software>kafka>servers' ")
        return kafka_server_list, port_list

    @staticmethod
    def validate(phase: str):
        """ Perform validtions """

        # Perform RPM validations
        pass

    @staticmethod
    def post_install():
        """ Performs post install operations """

        # check whether zookeeper and kafka are running
        ServiceV().validate("isrunning", ["kafka-zookeeper.service", "kafka.service"])

        # Check python packages and install if something is missing
        cmd = "pip3 freeze"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, retcode = cmd_proc.run()
        result = stdout.decode("utf-8") if retcode == 0 else stderr.decode("utf-8")
        with open('/opt/seagate/cortx/utils/conf/requirements.txt') as f:
            pkgs = f.readlines()
            # pkgs will have \n in every string. Need to remove that
            for package in enumerate(pkgs):
                if result.find(package[1][:-1]) == -1:
                    raise SetupError(errno.EINVAL, "Required python package %s is missing" % package[1][:-1])
        return 0

    @staticmethod
    def init():
        """ Perform initialization """
        return 0

    @staticmethod
    def config(conf_url):
        """ Performs configurations """

        # Message Bus Config
        kafka_server_list, port_list = Utils._get_kafka_server_list(conf_url)
        if kafka_server_list == None:
            raise SetupError(errno.EINVAL, "No Kafka setup info provided")
        return Utils._create_msg_bus_config(kafka_server_list, port_list)

    @staticmethod
    def test():
        """ Perform configuration testing """
        from cortx.setup import MessageBusTest
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
        """ Reset all the data that was created after post install """

        from cortx.utils.conf_store import Conf
        Conf.load("index", "json:///etc/cortx/message_bus.conf")
        server = Conf.get("index", 'message_broker>cluster[0]>server')
        if not server:
            import sys
            print("Reset/Cleanup already done or config file not found!")
            sys.exit(0)

        # list all topics created
        topic_list_cmd = f"/opt/kafka/bin/kafka-topics.sh --list --bootstrap-server {server}:9092"
        cmd_proc = SimpleProcess(topic_list_cmd)
        res_op, res_err, res_rc = cmd_proc.run()
        if res_rc != 0:
            raise SetupError(errno.EINVAL, f"Unable to list topics created. Make sure that kafka servers are running!")
        topics = ",".join([x for x in res_op.decode("utf-8").split('\n') if x])

        # delete topics
        if topics:
            cmd = f"/opt/kafka/bin/kafka-topics.sh --delete --topic {topics} --bootstrap-server {server}:9092"
            cmd_proc = SimpleProcess(cmd)
            res_op, res_err, res_rc = cmd_proc.run()
            if res_rc != 0:
                raise SetupError(errno.EIO, f"Error while deleting topic!")
        print("Reset completed successfully!")
        return 0

    @staticmethod
    def cleanup():
        """ Cleanup message bus config and logs. """

        # delete data/config stored
        cmd = "rm -rf /etc/cortx/message_bus.conf"
        cmd_proc = SimpleProcess(cmd)
        stdout, stderr, retcode = cmd_proc.run()
        if retcode != 0:
            raise SetupError(errno.EIO,
                             "Error while deleting config file")
        print("Cleanup completed successfully!")
        return 0
