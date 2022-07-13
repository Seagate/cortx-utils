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
import argparse
import inspect
import sys
import traceback
from argparse import RawTextHelpFormatter
from cortx.utils.activity_tracker.activity_store import Activity
from cortx.utils.activity_tracker.error import ActivityError


class ActivityCli:
    """CLI for the Activity Store."""

    _index = "Activity_cli"

    @staticmethod
    def init(url: str):
        """Load ActivityStore URL."""
        Activity.init(url)

    @staticmethod
    def create(args):
        """Set Key Value."""
        if len(args.args) < 2:
            raise ActivityError(errno.EINVAL, "Insufficient args for create")
        resource = args.args[0]
        description = args.args[1]
        activity = Activity.create(resource, description)
        return activity.id

    @staticmethod
    def update(args) -> str:
        """Updates value for the given keys."""
        activity_id = args.args[0]
        pct_complete = args.args[1]
        status = args.args[2]
        activity = Activity.get(activity_id)
        Activity.update(activity, pct_complete, status)

    @staticmethod
    def start(args):
        """Starts the Activity."""
        activity_id = args.args[0]
        activity = Activity.get(activity_id)
        Activity.start(activity)

    @staticmethod
    def show(args):
        """Returns activity details present in store."""
        activity_id = args.args[0]
        activity = Activity.get(activity_id)
        return activity.payload.json

    @staticmethod
    def search(args):
        """Searches for a activity as per given criteria."""
        resource_path = args.args[0]
        filters = args.args[1].split(',')
        activity_list = Activity.search(resource_path, filters)
        return activity_list

    @staticmethod
    def finish(args):
        """Completes the Activity."""
        activity_id = args.args[0]
        activity = Activity.get(activity_id)
        Activity.finish(activity)


class CreateCmd:
    """Create Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('create', help=
            "Create Activity for the given resource\n"
            "# activity create '123>1>2>3'\n\n")
        s_parser.set_defaults(func=ActivityCli.create)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class StartCmd:
    """Start Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('start', help=
            "Starts the given Activity. Example command:\n"
            "# activity start '123>1>2>3>222.222'\n\n")
        s_parser.set_defaults(func=ActivityCli.start)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class FinishCmd:
    """Finish Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('finish', help=
            "Marks the given Activity complete. Example command:\n"
            "# activity finish '123>1>2>3>222.222'\n\n")
        s_parser.set_defaults(func=ActivityCli.finish)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


class UpdateCmd:
    """Update Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('update', help=
            "Updates the given Activity complete. Example command:\n"
            "# activity update '123>1>2>3>222.222 50 'reading...''\n\n")
        s_parser.set_defaults(func=ActivityCli.update)
        s_parser.add_argument('args', nargs='+', default=[], help='args')

class SearchCmd:
    """Search Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('search', help=
            "Lists the Activitys for given resource. Example command:\n"
            "# activity search '123>1>2>3>'\n\n")
        s_parser.set_defaults(func=ActivityCli.search)
        s_parser.add_argument('args', nargs='+', default=[], help='args')

class ShowCmd:
    """Show Cmd Structure."""

    @staticmethod
    def add_args(sub_parser) -> None:
        s_parser = sub_parser.add_parser('show', help=
            "Shows the Activity information. Example command:\n"
            "# activity show '123>1>2>3>222.222'\n\n")
        s_parser.set_defaults(func=ActivityCli.show)
        s_parser.add_argument('args', nargs='+', default=[], help='args')


def main():
    # Setup Parser
    parser = argparse.ArgumentParser(description='Activity CLI',
        formatter_class=RawTextHelpFormatter)
    parser.add_argument('url', help='URL for the ActivityStore backend')
    sub_parser = parser.add_subparsers(title='command',
        help="represents the action e.g. create, start, update, finish",
            dest='command')

    # Add Command Parsers
    members = inspect.getmembers(sys.modules[__name__])
    for name, cls in members:
        if name != "Cmd" and name.endswith("Cmd"):
            cls.add_args(sub_parser)

    # Parse and Process Arguments
    try:
        args = parser.parse_args()
        ActivityCli.init(args.url)
        out = args.func(args)
        if out is not None and len(out) > 0:
            print(out)
        return 0

    except ActivityError as e:
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
