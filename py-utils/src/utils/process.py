#!/usr/bin/env python3

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

import subprocess


class Process:
    def __init__(self, cmd):
        self._cmd = cmd

    def run(self):
        pass


class SimpleProcess(Process):

    """Execute process and provide output."""
    def __init__(self, cmd):
        super().__init__(cmd)
        self.shell = False
        self.cwd = None
        self.timeout = None
        self.env = None
        self.universal_newlines = None
        self._cp = None
        self._output = None
        self._err = None
        self._returncode = None

    def run(self, **args):
        """This will can run simple process."""
        for key, value in args.items():
            setattr(self, key, value)

        try:
            cmd = self._cmd.split() if type(self._cmd) is str else self._cmd
            self._cp = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=self.shell, cwd=self.cwd,
                timeout=self.timeout, check=False, env=self.env,
                universal_newlines=self.universal_newlines)

            self._output = self._cp.stdout
            self._err = self._cp.stderr
            self._returncode = self._cp.returncode
            return self._output, self._err, self._returncode
        except Exception as e:
            self._err = f"SubProcess Error: {e}"
            self._output = ""
            self._returncode = -1
            return self._output, self._err, self._returncode


class PipedProcess(Process):

    """Execute process with pipe and provide output."""
    def run(self, **args):
        # TODO:
        pass
