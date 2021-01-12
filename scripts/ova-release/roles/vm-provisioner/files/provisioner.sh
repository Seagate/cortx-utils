#!/bin/bash

yum install -y python3
python3 -m venv venv_cortx
source venv_cortx/bin/activate
pip3 install -U git+https://github.com/Seagate/cortx-prvsnr@cortx-1.0#subdirectory=api/python
provisioner --version

./script
