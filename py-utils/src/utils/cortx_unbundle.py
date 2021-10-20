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
# please email opensource@seagate.com or cortx-questions@seagate.com

import os
import sys
import errno
import tarfile
import argparse
from argparse import RawTextHelpFormatter


class CORTXUnbundleError(Exception):
    """ Generic Exception with error code and output """

    def __init__(self, rc, message, *args):
        self._rc = rc
        self._desc = message % (args)

    @property
    def rc(self):
        return self._rc

    @property
    def desc(self):
        return self._desc

    def __str__(self):
        if self._rc == 0:
            return self._desc
        return "error(%d): %s" %(self._rc, self._desc)


class CORTXUnbundle:

    _output_dir = "/tmp/support_bundle"

    @staticmethod
    def extract_bundle(bundle_id, target_path, components):
        """Extract the Support Bundle tarfile."""
        if 'file://' not in target_path:
            raise CORTXUnbundleError(errno.EINVAL, "\n\nTarget path should be in file format.\n"
                "Please specify the absolute target path.\n"
                "For example:-\n"
                "file:///var/cortx/support_bundle\n")
        path = target_path.split('//')[1]
        bundle_path = os.path.join(path, bundle_id)
        if not os.path.exists(bundle_path):
            raise CORTXUnbundleError(errno.EINVAL, f"Bundle Path:{bundle_path} doesn't exist."
                                     "Please check the Bundle ID is correct or not.")
        os.makedirs(CORTXUnbundle._output_dir, exist_ok=True)
        sb_tarfile = ''
        for _, _, files in os.walk(bundle_path):
            for file in files:
                if file.endswith('.tar.gz'):
                    sb_tarfile = os.path.join(bundle_path, file)
        if not sb_tarfile:
            raise CORTXUnbundleError(errno.EINVAL,
                                     f"No tarfile present to extract at path:{bundle_path}")
        if not components:
            tar = tarfile.open(sb_tarfile)
            tar.extractall(path=CORTXUnbundle._output_dir)
            tar.close()
        else:
            for component in components:
                tar = tarfile.open(sb_tarfile, 'r')
                for member in tar.getmembers():
                    if f"{component}.tar.gz" in member.name:
                        tar.extract(member.name, CORTXUnbundle._output_dir)
        for root, _, files in os.walk(CORTXUnbundle._output_dir):
            for file in files:
                if file.endswith('.tar.gz'):
                    comp_tarfile = os.path.join(root, file)
                    t = tarfile.open(comp_tarfile)
                    t.extractall(path=root)
                    t.close()
        print(f"Successfully extracted the SB tarfile at path:{CORTXUnbundle._output_dir}")

    @staticmethod
    def parse_args():
        """
        Parse and return available argument
        Parameters:
        bundle_id: Unique bundle id.
        target_path: Path where the generated support bundle tar file is present.
        componenets: (Optional parameter) list the components that need to be unbundled.
                     By Default the complete tarball will be extracted.
        """
        parser = argparse.ArgumentParser(description='Extract the Support Bundle.', \
        formatter_class=RawTextHelpFormatter)
        parser.add_argument('-b', '--bundle_id', required=True, \
            help='Bundle ID for Support Bundle')
        parser.add_argument('-t', '--location', required=True, \
            help="Location where CORTX support bundle will be present.")
        parser.add_argument('-c', '--components', default=[], \
            help="(Optional parameter) list the"\
            +"components that need to be unbundled. By Default"\
            +"the complete tarball will be extracted.")
        args=parser.parse_args()
        return args

def main():
    args = CORTXUnbundle.parse_args()
    CORTXUnbundle.extract_bundle(bundle_id=args.bundle_id,
                                 target_path=args.location,
                                 components=args.components)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)
