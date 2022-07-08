#!/bin/env python3
import sys
import re
import subprocess
from platform import python_version
# python_path = sys.executable
python_path = sys.path
# python_path.extend(['/usr/lib/python/site-packages', '/usr/lib/python2.7/site-packages'])
# print(python_path)
py_tmpl = re.compile(r'^/usr/lib/python(\d*[.,]{0,1}\d*)/site-packages$')

py_install_path = [ path for path in python_path if py_tmpl.match(path)] 
print(py_install_path)
# py_version = python_version()

## Replace <INSTALL_PATH> with cortx installation path. example: /opt/seagate
install_path=<INSTALL_PATH>
cortx_path= install_path + /cortx/
utils_path= cortx_path + /utils

# # Create /etc/cortx. This will be used for storing message_bus.conf file.
subprocess.run("/bin/mkdir", "-p", "/etc/cortx")

# # Copy the setup_cli.py as utils_setup.
subprocess.run("/bin/mkdir", "-p", utils_path + "/bin/")
subprocess.run("/bin/ln", "-sf", py_install_path[0] + "/cortx/setup/utils_setup.py", utils_path+ "/bin/utils_setup")
subprocess.run("/bin/chmod", "+x", utils_path + "/bin//utils_setup")

# # Copy the message_bus_server.py as message_bus_server.
subprocess.run("/bin/ln", "-sf", py_install_path[0] + "/cortx/utils/utils_server/utils_server.py", utils_path + "/bin/utils_server")
subprocess.run("/bin/chmod", "+x", utils_path + "/bin/utils_server")

# # Copy the cortx_support_bundle.py as cortx_support_bundle
subprocess.run("/bin/ln", "-sf", py_install_path[0] + "/cortx/support/cortx_support_bundle.py", utils_path + "/bin/cortx_support_bundle")
subprocess.run("/bin/chmod", "+x", utils_path + "/bin/cortx_support_bundle")

# # Copy cortx.conf file to /etc/cortx.
if not os.path.exists("/etc/cortx/cortx.conf"):
    subprocess.run("cp", "-n", utils_path + "/conf/cortx.conf.sample", "/etc/cortx/cortx.conf")

# # Copy support/utils_support_bundle.py to $utils_path/bin.
subprocess.run("/bin/ln", "-sf", py_install_path[0] + "/cortx/support/utils_support_bundle.py", utils_path + "/bin/utils_support_bundle")
subprocess.run("/bin/chmod", "+x", utils_path + "/bin/utils_support_bundle")

# # Replace cortx path to support_bundle.yaml.
subprocess.run("sed", "-i", "-e", "s|<CORTX_PATH>|${cortx_path}|g", utils_path + "/conf/support_bundle.yaml")

# # Copy rsyslog config to /etc/rsyslog.d.
if not os.path.exists("/etc/rsyslog.d"):
    subprocess.run("mkdir", "/etc/rsyslog.d") 
subprocess.run("cp", "-n", utils_path + "/conf/0-support_bundle.conf", "/etc/rsyslog.d")
