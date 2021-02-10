#!/bin/bash
#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#


set -ex

#yum install -y ruby-devel gcc make rpm-build rubygems python36
yum --enablerepo=centos-sclo-rh install rh-ruby23 rh-ruby23-ruby-devel gcc make rpm-build rubygems -y
cat <<EOF >>rh-ruby23.sh
#!/bin/bash
source /opt/rh/rh-ruby23/enable
export X_SCLS="$(scl enable rh-ruby23 "echo $X_SCLS")"
EOF

source rh-ruby23.sh
cp rh-ruby23.sh /etc/profile.d/


# issues with pip>=10:
# https://github.com/pypa/pip/issues/5240
# https://github.com/pypa/pip/issues/5221
python3 -m pip install -U pip setuptools

gem install --no-ri --no-rdoc rake fpm

rm -rf /var/cache/yum
