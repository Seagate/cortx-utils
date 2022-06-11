# CORTX Python common library.
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

import argparse
import inspect


class Cmd:
  """Comman."""

  def __init__(self, args: dict):
    self._args = args

  @staticmethod
  def get_command(module, desc: str, argv: dict):
    """Return the Command after parsing the command line."""

    parser = argparse.ArgumentParser(desc)
    subparsers = parser.add_subparsers()

    cmds = inspect.getmembers(module)
    cmds = [(x, y) for x, y in cmds if x.endswith("Cmd") and x != "Cmd"]
    for _, cmd in cmds:
      parser1 = subparsers.add_parser(cmd.name, help='%s %s' % (desc, cmd.name))
      parser1.set_defaults(command=cmd)
      cmd.add_args(parser1)

    args = parser.parse_args(argv)
    return args.command(args)
