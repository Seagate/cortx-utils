import os
import sys
import argparse
import subprocess
import shlex
import tarfile
import time

from sb_config import SB_FILE_PATH, UTILS_TEST_DIR, CURR_DIR


class SupportBundleError(Exception):

    """Generic Exception with error code and output."""

    def __init__(self, rc, message, *args):
        """Initialize with custom error message and return code."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Format error string."""
        print("SupportBundleError(%d): %s" %(self._rc, self._desc))

class SupportBundleInterface:

    """ SupportBundle interface to generate a support bundle of cortx logs,
        in a containerised env.

        For example: python3 sb_interface.py --generate

    """
    def setup(self):
        self.build_shared_storageclass()
        self.build_sb_image()

    def process(self):
        # Execute the deploy_sb_pod.sh shell script to start the support_bundle pod.
        cmd = f"{UTILS_TEST_DIR}/support_bundle/deploy.sh --sb_pod"
        _, _, rc = self._run_command(cmd)
        if rc != 0:
            msg = "Failed to deploy the supoort-bundle pod."
            raise SupportBundleError(1, msg)
        time.sleep(10)
        if os.path.exists(SB_FILE_PATH):
            print(f"Support Bundle generated successfully at path:{SB_FILE_PATH} !!!")
        else:
            msg = "Cortx Logs tarfile is not generated at specified path."
            raise SupportBundleError(1, msg)

    def build_shared_storageclass(self):
        cmd = f"{UTILS_TEST_DIR}/support_bundle/deploy.sh --pvc"
        response, err, rc = self._run_command(cmd)
        if rc != 0 :
            msg = f"Failed in Building PV-claim. ERROR:{err}"
            raise SupportBundleError(1, msg)
        if response:
            print(response)
            print("Waiting for the containers to start up...")
            time.sleep(5)

    def build_sb_image(self):
        dockerfile_dir = f"{UTILS_TEST_DIR}/support_bundle"
        os.chdir(dockerfile_dir)
        cmd = f"./deploy.sh --sb_image"    
        response, err, rc = self._run_command(cmd)
        if rc != 0:
            msg = f"Failed to build support-bundle image. ERROR:{err}"
            raise SupportBundleError(1, msg)
        if response:
            print("==== Building Support-bundle Image. ====")
            print(response)
        os.chdir(CURR_DIR)

    def cleanup(self):
        cmd = f"{UTILS_TEST_DIR}/support_bundle/deploy.sh --delete_pod"
        _, _, rc = self._run_command(cmd)
        if rc != 0:
            msg = "Failed to delete the support-bundle pod"
            raise SupportBundleError(1, msg)

    def _run_command(self, command):
        """Run the command and get the response and error returned."""
        cmd = shlex.split(command) if isinstance(command, str) else command
        process = subprocess.run(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, shell=False)
        output = process.stdout.decode('UTF-8')
        error = process.stderr.decode('UTF-8')
        returncode = process.returncode
        return output, error, returncode

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description='''Bundle cortx logs ''')
        parser.add_argument('--generate', help='generate support bundle',
                            action='store_true')
        args=parser.parse_args()
        return args

def main():
    args = SupportBundleInterface.parse_args()
    SupportBundleObj = SupportBundleInterface()
    if args.generate:
        SupportBundleObj.setup()
        SupportBundleObj.process()
        SupportBundleObj.cleanup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print(f"\n\nWARNING: User aborted command. Partial data " \
            f"save/corruption might occur. It is advised to re-run the" \
            f"command. {e}")
        sys.exit(1)

