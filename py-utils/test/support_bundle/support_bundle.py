#! /usr/bin/python3

import tarfile
import json
import os
import sys


class SupportBundleError(Exception):
    """Generic Exception with error code and output."""

    def __init__(self, rc, message, *args):
        """Initialize with custom error message and return code."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Format error string."""
        if self._rc == 0: return self._desc
        print("SupportBundleError(%d): %s" %(self._rc, self._desc))

class SupportBundle(object):

    @staticmethod
    def read_bundle_info():
        SB_DATA_PATH = "/var/cortx/support_bundle/data/"
        tmp_data_file = f"{SB_DATA_PATH}/bundle_info.json"
        with open(tmp_data_file) as json_file:
            bundle_data = json.load(json_file)
            return bundle_data

    @staticmethod
    def generate_tar(bundle_info):
        components = bundle_info["components"]
        bundle_path = bundle_info["bundle_path"]
        bundle_id = bundle_info["bundle_id"]
        CORTX_LOG_DIR = "/var/log"
        for component in components:
            if component != "all":
                sb_file_path = bundle_path + f"/{component}-support_bundle-{bundle_id}.tar.gz"
                archieve_dir = f"{CORTX_LOG_DIR}/cortx/{component}"
            else:
                sb_file_path = bundle_path + f"/cortx-support_bundle-{bundle_id}.tar.gz"
                archieve_dir = CORTX_LOG_DIR
            try:
                if os.path.isdir(archieve_dir):
                    with tarfile.open(sb_file_path, "w:gz") as tar_handle:
                        for root, _, files in os.walk(archieve_dir):
                            for file in files:
                                tar_handle.add(os.path.join(root, file))
            except Exception as err:
                raise SupportBundleError(1, str(err))

if __name__ == "__main__":
    try:
        bundle_info = SupportBundle.read_bundle_info()
        SupportBundle.generate_tar(bundle_info)
    except KeyboardInterrupt:
        print("Failed to generate support bundle.")
        sys.exit(0)
    except Exception as err:
        print(err)
        sys.exit(1)

