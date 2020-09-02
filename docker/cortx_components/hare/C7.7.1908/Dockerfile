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

FROM ssc-vm-0279.colo.seagate.com:5000/motr:C7.7.1908

ENV HARE_VENV_DIR=$HOME/.hare-venv

RUN yum install -y python36 python36-devel python36-pip python36-PyYAML
RUN mkdir $HARE_VENV_DIR \
    && python3 -m venv $HARE_VENV_DIR

# PyYAML - for cfgen
# flake8 - for hax
# mypy   - for hax
# ply    - for motr
# wheel  - for hax
RUN source $HARE_VENV_DIR/bin/activate \
    && pip3 install PyYAML flake8 mypy ply wheel

ADD https://github.com/dhall-lang/dhall-haskell/releases/download/1.26.1/dhall-1.26.1-x86_64-linux.tar.bz2      /var/cache
ADD https://github.com/dhall-lang/dhall-haskell/releases/download/1.26.1/dhall-json-1.4.1-x86_64-linux.tar.bz2  /var/cache
RUN for f in /var/cache/dhall*.tar*; do tar -C /usr/local -xf $f; done

COPY docker-entrypoint /usr/local/bin/
