#!/usr/bin/env python3

# CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
#
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
import os
import shutil
import tarfile
import argparse
import time
from datetime import datetime

from cortx.utils.conf_store import Conf
from cortx.utils.errors import UtilsError
from cortx.utils.discovery import Discovery
from cortx.utils.discovery.request_handler import req_register


class ManifestBundleError(UtilsError):
    """ManifestBundleError exception with error code and output."""

    def __init__(self, rc, message, *args):
        """Initialize ManifestBundleError."""
        super().__init__(rc, message, *args)


class ManifestSupportBundle:
    """Generate support bundle for manifest."""
    _tmp_dir = '/tmp/cortx'
    _default_path = '%s/support_bundle/' % _tmp_dir
    _tar_name = 'manifest'
    _tmp_src = '%s/%s/' % (_tmp_dir, _tar_name)
    _conf_file = 'json:///etc/cortx/cluster.conf'

    @staticmethod
    def generate(bundle_id: str, target_path: str):
        """Generate a tar file."""
        if os.path.exists(ManifestSupportBundle._tmp_src):
            ManifestSupportBundle.__clear_tmp_files()
        bundle_time = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
        ManifestSupportBundle.__collect_manifest_data(bundle_id, target_path,
            bundle_time)
        ManifestSupportBundle.__generate_tar(bundle_id, target_path, bundle_time)
        ManifestSupportBundle.__clear_tmp_files()

    @staticmethod
    def get_status(bundle_id: str):
        """Get status of support bundle."""
        status = None
        req_id = 'sb_%s' % bundle_id
        manifest_id = req_register.get(['%s>manifest_id' % req_id])
        manifest_status = Discovery.get_gen_node_manifest_status(manifest_id[0])
        # Extract manifest status from the message.
        # Example : "Failed - error(22): Invalid rpath 'node>abc'"
        status = manifest_status.split(' ')[0]
        if status != 'In-progress':
            return status
        return None

    @staticmethod
    def __collect_manifest_data(bundle_id: str, target_path: str, bundle_time: str):
        """Collecting manifest summary data using the discovery library."""
        directory = os.path.dirname(ManifestSupportBundle._tmp_src)
        if not os.path.exists(directory):
            os.makedirs(directory)
        tar_name, file_name = ManifestSupportBundle.__generate_file_names(
            bundle_id, bundle_time)
        file_path = ManifestSupportBundle._tmp_src + file_name
        tar_file = os.path.join(target_path, tar_name + '.tar.gz')
        manifest_id = Discovery.generate_node_manifest(
            store_url = 'json://%s' % file_path)
        # Update bundle request info with discovery request_id
        ManifestSupportBundle.__update_request_info(bundle_id, manifest_id,
            tar_file)
        while not Discovery.get_gen_node_manifest_status(manifest_id)\
            .startswith(('Success', 'Failed')): time.sleep(0.5)

    @staticmethod
    def __update_request_info(bundle_id: str, manifest_id: str, tar_file: str):
        """Updates new request information with discovery request_id."""
        req_id = 'sb_%s' % bundle_id
        req_info = {
            'manifest_id': manifest_id,
            'tar_file': tar_file,
            'time': datetime.strftime(
                datetime.now(), '%Y-%m-%d %H:%M:%S')
        }
        req_register.set(['%s' % req_id], [req_info])

    @staticmethod
    def __generate_tar(bundle_id: str, target_path: str, bundle_time: str):
        """Generate tar.gz file at given path."""
        component = 'manifest'
        target_path = target_path if target_path is not None \
            else ManifestSupportBundle._default_path
        target_path = os.path.join(target_path, component)
        tar_name, _ = ManifestSupportBundle.__generate_file_names(
            bundle_id, bundle_time)
        tar_file_name = os.path.join(target_path, tar_name + '.tar.gz')
        if not os.path.exists(target_path):
            os.makedirs(target_path)
        with tarfile.open(tar_file_name, 'w:gz') as tar:
            tar.add(ManifestSupportBundle._tmp_src,
                arcname=os.path.basename('/' + tar_name))

    @staticmethod
    def __generate_file_names(bundle_id: str, bundle_time: str):
        """Will return a unique file name for every support bundle request."""
        Conf.load('cluster', ManifestSupportBundle._conf_file, skip_reload=True)
        cluster_conf = Conf.get('cluster', 'server_node')
        cluster_id = cluster_conf['cluster_id']
        enclosure_id = cluster_conf['storage']['enclosure_id'] if 'storage' in \
            cluster_conf else 'NA'
        hostname = ManifestSupportBundle.__get_private_hostname(cluster_conf)
        tar_name = 'manifest_{0}_SN-{1}_Server-{2}_{3}'.format(bundle_time,
            cluster_id, hostname, bundle_id)
        if enclosure_id:
            tar_name = 'manifest_{0}_SN-{1}_Server-{2}_plus_Encl-{3}_{4}'.\
                format(bundle_time, cluster_id, hostname, enclosure_id, bundle_id)
        file_name = '{0}.json'.format(tar_name.replace('manifest_', 'MS_')\
            .replace(f'_{bundle_id}','').replace('plus_',''))
        return tar_name, file_name

    @staticmethod
    def __get_private_hostname(cluster_conf):
        """Returning private hostname."""
        try:
            private_fqdn = cluster_conf['network']['data']['private_fqdn']
            hostname = private_fqdn.split('.')[0]
        except:
            hostname = 'NA'
        return hostname

    @staticmethod
    def __clear_tmp_files():
        """Clean temporary files created by the support bundle."""
        shutil.rmtree(ManifestSupportBundle._tmp_src)

    @staticmethod
    def parse_args():
        """
        Parse and return available argument
        Parameters:
        action: used to create| delete| status| cancel the support bundle
                script.
        bundle_id: Unique bundle id.
        path: Path where the generated support bundle tar file should
              be stored.
        modules: (Optional parameter) list the number of submodules
                 that need to be bundled. By Default all the modules
                 in the components will be bundled.
        """
        parser = argparse.ArgumentParser(description='''Bundle manifest files ''')
        parser.add_argument('action', help="Action can be create| status|"\
            + "delete| cancel")
        parser.add_argument('bundle_id', help="Unique bundle id")
        parser.add_argument('path', help="Path where the generated support"\
            +"bundle tar file should be stored", nargs='?',
            default="/var/seagate/cortx/support_bundle/")
        parser.add_argument('--modules', help="(Optional parameter) list the"\
            +"number of submodules that need to be bundled. By Default all"\
            +"the modules in the components will be bundled.")
        args=parser.parse_args()
        return args


def main():
    args = ManifestSupportBundle.parse_args()
    if args.action == 'create':
        ManifestSupportBundle.generate(bundle_id=args.bundle_id, target_path=args.path)
    elif args.action == 'status':
        ManifestSupportBundle.get_status(bundle_id=args.bundle_id)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)
