import os
import string
import random
import shutil
import subprocess
import shlex
import time
import json

from sb_config import SB_DATA_PATH, UTILS_TEST_DIR, CURR_DIR
from bundle import Bundle
from response import Response


class SupportBundleError(Exception):
    """Generic Exception with error code and output."""

    def __init__(self, rc, message, *args):
        """Initialize with custom error message and return code."""
        self._rc = rc
        self._desc = message % (args)

    def __str__(self):
        """Format error string."""
        print("SupportBundleError(%d): %s" %(self._rc, self._desc))

class SupportBundle:
    """ SupportBundle interface to generate a support bundle of cortx logs,
        in a containerised env.

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
        print("Successfully deployed support-bundle pod. !!!")

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
        cmd = "./deploy.sh --sb_image"    
        response, err, rc = self._run_command(cmd)
        if rc != 0:
            msg = f"Failed to build support-bundle image. ERROR:{err}"
            raise SupportBundleError(1, msg)
        if response:
            print("==== Building Support-bundle Image. ====")
            print(response)
        os.chdir(CURR_DIR)

    @staticmethod
    def cleanup():
        # Delete support-bundle tar, if already present
        if os.path.isdir(SB_DATA_PATH):
            shutil.rmtree(SB_DATA_PATH)
        os.mkdir(SB_DATA_PATH)

    @staticmethod
    def _run_command(command):
        """Run the command and get the response and error returned."""
        cmd = shlex.split(command) if isinstance(command, str) else command
        process = subprocess.run(cmd, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, shell=False)
        output = process.stdout.decode('UTF-8')
        error = process.stderr.decode('UTF-8')
        returncode = process.returncode
        return output, error, returncode

    @staticmethod
    def _generate_bundle_id():
        """Generate Unique Bundle ID."""
        alphabet = string.ascii_lowercase + string.digits
        return f"SB{''.join(random.choices(alphabet, k=8))}"

    @staticmethod
    def generate(comment: str, **kwargs):
        """
        Initializes the process for Generating Support Bundle.

        comment:        Mandatory parameter, reason why we are generating
                        support bundle
        components:     Optional paramter, If not specified SB will be generated
                        for all components.You can specify multiple components
                        also Eg: components = ['utils', 'provisioner']
        return:         bundle_obj
        """
        components = ''
        # Cleanup old tmp files.
        SupportBundle.cleanup()
        tmp_data_file = f"{SB_DATA_PATH}/bundle_info.json"
        for key, value in kwargs.items():
            if key == 'components':
                components = value
        if not components:
            components = ["all"]
        bundle_id = SupportBundle._generate_bundle_id()
        bundle_obj = Bundle(bundle_id=bundle_id, bundle_path=SB_DATA_PATH,
                            comment=comment)
        # dump bundle info to a json file, for support-bundle pod to read.
        data = {}
        data["bundle_id"] = bundle_obj.bundle_id
        data["bundle_path"] = bundle_obj.bundle_path
        data["components"] = components
        with open(tmp_data_file, 'w') as outfile:
            json.dump(data, outfile)
        print("Deploying Support-bundle Pod.")
        SupportBundle().setup()
        SupportBundle().process()
        return bundle_obj

    @staticmethod
    def get_bundle_status(bundle_id):
        status = "Success"
        output = ""
        sb_file_path = f"{SB_DATA_PATH}/cortx-support_bundle-{bundle_id}.tar.gz"
        tmp_data_file = f"{SB_DATA_PATH}/bundle_info.json"
        with open(tmp_data_file) as json_file:
            bundle_data = json.load(json_file)
        components = bundle_data["components"]
        for component in components:
            if component != "all":
                sb_file_path = f"{SB_DATA_PATH}/{component}-support_bundle-{bundle_id}.tar.gz"
            if not os.path.exists(sb_file_path):
                status = "Failed"
                output = (f"Support-bundle not generated."
                          f"Please check /var/log/{component} dir exists or not")
        if status == "Success":
            output = f"Support Bundle generated successfully at path: {sb_file_path}"
        return Response(status=status, output=output)

    @staticmethod
    def get_status(bundle_id: str = None):
        """
        Initializes the process for Displaying the Status for Support Bundle
        bundle_id:  Using this will fetch bundle status :type: string
        """
        status_obj = SupportBundle.get_bundle_status(bundle_id)
        return status_obj
        
