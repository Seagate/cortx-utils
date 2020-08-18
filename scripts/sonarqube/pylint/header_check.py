#!/usr/bin/python3
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

import re
from pylint.interfaces import IRawChecker
from pylint.checkers import BaseChecker

class CopyrightChecker(BaseChecker):
    """ Check file for copyright notice
    """

    __implements__ = IRawChecker

    name = 'custom_copy'

    msgs = {
        'W9001': ('Missing copyright header',
                  'Used when a module of seagate has no copyright header.',
                  'missing-copyright-header')
    }

    options = ()

    commentsCopyright = "# COPYRIGHT [0-9]* SEAGATE LLC"

    def process_module(self, node):
        """process a module
        the module's content is accessible via node.file_stream.read() function
        """
        text = node.file_stream.read()
        if not re.search(self.commentsCopyright, text):
            self.add_message('W9001', line=1)

def register(linter):
    """required method to auto register this checker"""
    linter.register_checker(CopyrightChecker(linter))