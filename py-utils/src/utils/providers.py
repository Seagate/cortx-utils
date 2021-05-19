#!/usr/bin/env python3

# CORTX-Py-Utils: CORTX Python common library.
# Copyright (c) 2021 Seagate Technology LLC and/or its Affiliates
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


class Request(object):
    """ Represents a request to be processed by Provider """

    def __init__(self, action, args, options=None):
        self._action = action
        self._args = args
        self.options = options

    def action(self):
        return self._action

    def args(self):
        return self._args

    def options(self):
        return self.options


class Response(object):
    """ Represents a response after processing of a request """
    # TODO:Wherever this class is used for raising the error; that will be
    #  replaced with proper CsmError type

    def __init__(self, rc=0, output=''):
        self._rc = int(rc)
        self._output = output

    def output(self):
        return self._output

    def rc(self):
        return self._rc

    def __str__(self):
        return '%d: %s' % (self._rc, self._output)
