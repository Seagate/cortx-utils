# from cortx.utils.conf_store import Conf
from cortx.utils.process import SimpleProcess
import subprocess
import pdb;pdb.set_trace()
# Conf.load("index", "yaml:///tmp/s3.yaml")
Conf.load("index", "pillar://root@")

# 
# result_data = Conf.get_keys('index')
# result = Conf.get('index', 'version_config')
# result1 = Conf.get('index', 'version_config>version')

# CLI test
# result_data = subprocess.check_output(['conf', 'yaml:///tmp/s3.yaml', 'get', 'version_config'])
# result_data1 = subprocess.check_output(['conf', 'yaml:///tmp/s3.yaml', 'get', 'version_config>version'])

print("Program end")