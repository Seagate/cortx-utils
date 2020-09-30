#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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
import os
import sys
import traceback
from datetime import datetime

from cortx.utils.schema.conf import Conf


def usage():
    return """

Example:
Shorter parameter:
$ hac -v /my/spec/my_spec.json
$ hac –c /my/spec/dir -o cortx_ha.spec
$ hac –g cortx_ha.spec -o cortx_pcs.sh -t pcs
$ hac -c /opt/seagate/ha_files/files/ -b /my/spec/dir

Longer parameter:
$ hac --validate /opt/seagate/ha_files/files/csm.json
$ hac --compile /my/spec/dir --output compiled.json
$ hac --generate compiled.json --output cortx_pcs.sh --target pcs

"""

# TODO: make resource name case insensitive
# TODO: hac –d cortx_ha.spec -t pcs


def main():
    from cortx.utils.ha.hac.compile import Compiler  # pylint: disable=import-outside-toplevel
    from cortx.utils.ha.hac import generate  # pylint: disable=import-outside-toplevel
    from cortx.utils.ha.hac import const  # pylint: disable=import-outside-toplevel

    provider = {
        "pcs": generate.PCSGeneratorResource,
        "k8s": generate.KubernetesGenerator
    }

    try:
        Conf.init()
        arg_parser = argparse.ArgumentParser(usage="%(prog)s\n\n" + usage(),
                                             formatter_class=argparse.RawDescriptionHelpFormatter)
        arg_parser.add_argument("-v", "--validate", help="Check input files for syntax errors")
        arg_parser.add_argument("-t", "--target", default="pcs",
                                help="HA target to use. Example: pcs")
        arg_parser.add_argument("-c", "--compile", help="Path of ha_spec files.")
        arg_parser.add_argument("-o", "--output",
                                help="Final spec/rule file for generator/compiler")
        arg_parser.add_argument("-g", "--generate",
                                help="Generate script/rule for targeted HA tool. Eg: pcs")
        arg_parser.add_argument("-a", "--args_file",
                                help="Args file for generator for dynamic input values")
        arg_parser.add_argument("-r", "--resources", help="Enter resource list")
        args = arg_parser.parse_args()

        if args.generate is None:
            c = Compiler(args.compile, args.output, args.validate)
            if args.validate is None:
                c.parse_files()
                c.compile_graph()
                c.verify_schema()
                c.create_schema()
                c.draw_graph()
        else:
            com = provider[args.target](args.generate,
                                        args.output,
                                        args.args_file,
                                        args.resources)
            com.create_script()
    except Exception as e:
        # TODO: print traceback error properly
        with open(const.HAC_LOG, "w") as log:
            current_time = str(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            log.writelines(f"{current_time}:{traceback.format_exc()}")
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
