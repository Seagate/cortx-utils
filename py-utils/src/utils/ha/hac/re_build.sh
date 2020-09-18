#!/bin/bash

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
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

# Perform cleanup
rm -rf /var/lib/cortx/ha/script
mkdir -p /var/lib/cortx/ha/script

hac --compile /var/lib/cortx/ha/specs/ --output /var/lib/cortx/ha/compiled.json

if [ $? != 0 ]; then
    echo "Compilation of spec failed !!!"
    exit 1
fi

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/cortx-pcs.sh --args /var/lib/cortx/ha/args.yaml

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/lnet_c1_c2.sh --args /var/lib/cortx/ha/args.yaml --resources "lnet-c1 lnet-c2"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/hax_c1_c2.sh --args /var/lib/cortx/ha/args.yaml --resources "hax-c1 hax-c2"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/motr_iso_c1_c2.sh --args /var/lib/cortx/ha/args.yaml --resources "motr-ios-c1 motr-ios-c2"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/s3auth.sh --args /var/lib/cortx/ha/args.yaml --resources "s3auth"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/el_ha_st.sh --args /var/lib/cortx/ha/args.yaml --resources "els-search statsd haproxy"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/s3server.sh --args /var/lib/cortx/ha/args.yaml --resources "s3server-c1-1 s3server-c1-2 s3server-c1-3 s3server-c1-4 s3server-c1-5 s3server-c1-6 s3server-c1-7 s3server-c1-8 s3server-c1-9 s3server-c1-10 s3server-c1-11 s3server-c2-1 s3server-c2-2 s3server-c2-3 s3server-c2-4 s3server-c2-5 s3server-c2-6 s3server-c2-7 s3server-c2-8 s3server-c2-9 s3server-c2-10 s3server-c2-11"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/s3back.sh --args /var/lib/cortx/ha/args.yaml --resources "s3backprod s3backcons"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/sspl.sh --args /var/lib/cortx/ha/args.yaml --resources "sspl"

hac --generate /var/lib/cortx/ha/compiled.json  --output /var/lib/cortx/ha/script/csm.sh --args /var/lib/cortx/ha/args.yaml --resources "kibana-vip"

