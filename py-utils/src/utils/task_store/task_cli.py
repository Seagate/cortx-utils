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

import errno
import argparse
import inspect
import sys
import traceback
from argparse import RawTextHelpFormatter
from cortx.utils.task_store import Task
from cortx.utils.task_store import TaskError
from cortx.utils.schema import Format


class TaskCli:
    """ CLI for the Task Store """
    _index = "Task_cli"

    @staticmethod
    def init(url: str):
        """ Load TaskStore URL """
        Task.init(url)

    @staticmethod
    def create(args):
        """ Set Key Value """
        if len(args.args) < 2:
            raise TaskError(errno.EINVAL, "Insufficient args for create")
        resource = args.args[0]
        description = args.args[1]
        task = Task.create(resource, description)
        return task.id

    @staticmethod
    def update(args) -> str:
        """ Obtain value for the given keys """
        task_id = args.args[0]
        pct_complete = args.args[1]
        status = args.args[2]
        task = Task.get(task_id)
        Task.update(task, pct_complete, status)

    @staticmethod
    def start(args):
        """ Deletes given set of keys from the Taskig """
        task_id = args.args[0]
        task = Task.get(task_id)
        Task.start(task)

    @staticmethod
    def finish(args):
        """ Returns list of keys present in store """
        task_id = args.args[0]
        task = Task.get(task_id)
        task.finish()


class CreateCmd:
    """ Create Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('create', help=
            "Create Task for the given resource\n"
            "# task create '123>1>2>3'\n\n")
        s_parser.set_defaults(func=TaskCli.create)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class StartCmd:
    """ Set Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('start', help=
            "Starts the given Task. Example command:\n"
            "# task start '123>1>2>3>222.222'\n\n")
        s_parser.set_defaults(func=TaskCli.start)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class FinishCmd:
    """ Finish Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('finish', help=
            "Marks the given Task complete. Example command:\n"
            "# task finish '123>1>2>3>222.222'\n\n")
        s_parser.set_defaults(func=TaskCli.finish)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class UpdateCmd:
    """ Updarte Cmd Structure """

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('update', help=
            "Updates the given Task complete. Example command:\n"
            "# task update '123>1>2>3>222.222 50 'reading...''\n\n")
        s_parser.set_defaults(func=TaskCli.update)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


def main():
    # Setup Parser
    parser = argparse.ArgumentParser(description='Task CLI',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('url', help='URL for the TaskStore backend')
    sub_parser = parser.add_subparsers(title='command',
        help="represents the action from: create, start, update, finish", 
            dest='command')

    # Add Command Parsers
    members = inspect.getmembers(sys.modules[__name__])
    for name, cls in members:
        if name != "Cmd" and name.endswith("Cmd"):
            cls.add_args(sub_parser)

    # Parse and Process Arguments
    try:
        args = parser.parse_args()
        TaskCli.init(args.url)
        out = args.func(args)
        if out is not None and len(out) > 0:
            print(out)
        return 0

    except TaskError as e:
        sys.stderr.write("%s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        return e.rc

    except Exception as e:
        sys.stderr.write("%s\n\n" % str(e))
        sys.stderr.write("%s\n" % traceback.format_exc())
        return errno.EINVAL

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
