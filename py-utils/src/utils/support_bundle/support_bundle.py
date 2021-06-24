import os.path
import shutil
import tarfile
import errno

from cortx.utils.support_bundle.error import SupportBundleError


class SupportBundle:

    def __init__(self, path: str = "/tmp/cortx/support_bundle/", tar_name: str="py-utils" ):
        self.path = path
        self.tar_name = tar_name
        self.tmp_src = "/tmp/cortx/py-utils/"
        self.files_to_bundle = {
            "message_bus": "/var/log/cortx/utils/message_bus/MessageBus.log",
            "iem_and_rest":
                "/var/log/cortx/utils/utils_server/utils_server.log",
            "kafka": "/var/log/cortx/utils/utils_setup.log",
            "kafka_server": "/opt/kafka/config/server.properties",
            "kafka_zookeeper": "/opt/kafka/config/zookeeper.properties"
        }

    def generate_support_bundle(self):
        import pdb;pdb.set_trace()
        # MessageBus
        for key, value in self.files_to_bundle.items():
            print(value)
            self.copy_file(value)
        self.generate_tar()

    def copy_file(self, source: str, destination: str = None):
        if destination is None:
            destination = self.tmp_src + os.path.basename(source)
        try:
            shutil.copy2(source, destination)
        except FileNotFoundError as fe:
            print(fe)
            raise SupportBundleError(errno.EINVAL, "File not found %s", fe)

    def generate_tar(self):
        tar_file_name = self.path + self.tar_name + ".tar.gz"
        with tarfile.open(tar_file_name, "w:gz") as tar:
            tar.add(self.tmp_src, arcname=os.path.basename(self.tmp_src))

if __name__ == '__main__':
    sb_inst = SupportBundle()
    sb_inst.generate_support_bundle()
