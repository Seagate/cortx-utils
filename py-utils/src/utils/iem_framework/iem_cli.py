#!/usr/bin/env python3

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

import sys
import errno
import inspect
import argparse
import traceback
from argparse import RawTextHelpFormatter

from cortx.utils.schema import Format
from cortx.utils.iem_framework.error import EventMessageError
from cortx.utils.iem_framework.event_message import EventMessage


class IemCli:
    """ CLI for the IEM """

    @staticmethod
    def _get_empty_send_args():
        """
        Creates a dict of required parameters for send
        and initialises with None
        """
        blank_send_args: dict = {
            'component': None,
            'module': None,
            'event_id': None,
            'source_type': None,
            'severity': None,
            'message': None,
            'problem_cluster_id': None,
            'problem_site_id': None,
            'problem_rack_id': None,
            'problem_node_id': None,
            'problem_host': None,
            'event_time': None
        }
        return blank_send_args

    @staticmethod
    def _parse_send_args(args) -> dict:
        """ Maps values from cmd line args to send_args dict """

        send_args = IemCli._get_empty_send_args()
        try:
            send_args['component'], send_args['module'] = args.source.split(':')
            send_args['cluster'] = args.cluster
            send_args['source_type'], send_args['severity'] \
                = args.info.split(':')
            if ':' in args.contents:
                send_args['event_id'], send_args['message'] \
                    = args.contents.split(':')
            elif args.file:
                send_args['event_id'] = args.contents
                with open(args.file, 'r') as fd:
                    send_args['message'] = ''.join(fd.readlines())
            send_args['endpoints'] = args.endpoints
        except ValueError:
            raise EventMessageError(errno.EINVAL, "Invalid send arguments!")

        if args.location:
            cluster_id, site_id, node_id, rack_id, host = \
                args.location.split(':')
            send_args['problem_cluster_id'] = cluster_id
            send_args['problem_site_id'] = site_id
            send_args['problem_node_id'] = node_id
            send_args['problem_rack_id'] = rack_id
            send_args['problem_host'] = host

        return send_args

    @staticmethod
    def subscribe(component: str, message_server_endpoints: str, **filters):
        EventMessage.subscribe(component, message_server_endpoints, **filters)

    @staticmethod
    def send(args_parse):
        """ send IE message """

        send_args = IemCli._parse_send_args(args_parse)
        EventMessage.init(
            component=send_args['component'],
            source=send_args['source_type'],
            cluster_id=send_args['cluster'],
            message_server_endpoints=[send_args['endpoints']]
        )
        EventMessage.send(
            module=send_args['module'],
            event_id=send_args['event_id'],
            severity=send_args['severity'],
            message_blob=send_args['message'],
            problem_cluster_id=send_args['problem_cluster_id'],
            problem_site_id=send_args['problem_site_id'],
            problem_rack_id=send_args['problem_rack_id'],
            problem_node_id=send_args['problem_node_id'],
            problem_host=send_args['problem_host'],
            event_time=send_args['event_time']
        )

    @staticmethod
    def receive(args) -> str:
        """
        Receives IEM Message and returns to the caller, If file[-f] is passed,
        writes message to file and returns blank string to caller
        """
        IemCli.subscribe(component=args.source, message_server_endpoints=[args.endpoints])
        rec_data = ''
        event = ' '
        while event:
            try:
                event = EventMessage.receive()
                rec_data += Format.dump(event, 'json') + '\n' if event else '\n'
            except Exception:
                raise EventMessageError(
                    errno.EINVAL,
                    "Error occurred while receiving IEM data"
                )
        if args.file:
            with open(args.file, 'a') as fd:
                fd.write(rec_data)
                return ''

        return rec_data


class SendCmd:
    """ send Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser(
            'send',
            help="Sends iem message,for more help checkout iem send -h"
        )
        s_parser.set_defaults(func=IemCli.send)
        s_parser.add_argument('-f', '--file', help='<message_file>')
        # Argument_group marks following args as Required in iem send -h
        req_s_parser = s_parser.add_argument_group("Required arguments")
        req_s_parser.add_argument('-s', '--source', help='component:module')
        req_s_parser.add_argument('-i', '--info', help='source_type:severity')
        req_s_parser.add_argument('-c', '--contents', help='event_id:message')
        req_s_parser.add_argument('-l', '--location', \
            help='cluster_id:site_id:node_id:rack_id:host')
        req_s_parser.add_argument('-cluster', '--cluster', \
            help='cluster id')
        req_s_parser.add_argument('--endpoints', dest='endpoints',\
            help='ConfStore URL for the cluster.conf')


class ReceiveCmd:
    """ receive Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        r_parser = sub_parser.add_parser(
            'receive',
            help="Receives iem message, for more help checkout iem receive -h"
        )
        r_parser.set_defaults(func=IemCli.receive)
        r_parser.add_argument('-f', '--file', help="Redirects output to file")
        # Argument group to mark required cmdline arguments
        req_r_parser = r_parser.add_argument_group("Required arguments")
        req_r_parser.add_argument('-s', '--source', help='component_id')
        req_r_parser.add_argument('-i', '--info', help='source_type',
                                  choices=['S', 'H', 'F', 'O'])
        req_r_parser.add_argument('-cluster', '--cluster', \
            help='cluster id')
        req_r_parser.add_argument('--endpoints', dest='endpoints',\
            help='ConfStore URL for the cluster.conf')


def main():
    # Setup Parser
    parser = argparse.ArgumentParser(
        description="IEM CLI",
        formatter_class=RawTextHelpFormatter
    )
    sub_parser = parser.add_subparsers(
        title='command',
        help="represents the action from: send, receive",
        dest='command'
    )

    # Add Command Parsers
    members = inspect.getmembers(sys.modules[__name__])
    for name, cls in members:
        if name.endswith('Cmd'):
            cls.add_args(sub_parser)

    # Parse and Process Arguments
    try:
        args = parser.parse_args()
        output = args.func(args)
        if output:
            print(output)
        return 0
    except Exception as e:
        sys.stderr.write("%s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        return errno.EINVAL


if __name__ == '__main__':
    rc = main()
    sys.exit(rc)