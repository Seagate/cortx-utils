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

import errno
import subprocess
from subprocess import TimeoutExpired, CalledProcessError  # nosec

class Process:
    def __init__(self, cmd):
        self._cmd = cmd
        pass

    def run(self):
        pass


class SimpleProcess(Process):
    """ Execute process and provide output """
    def __init__(self, cmd):
        super(SimpleProcess, self).__init__(cmd)
        self.shell = False
        self.stdout = subprocess.PIPE
        self.realtime_output = False
        self.cwd = None
        self.timeout = None
        self.env = None
        self.universal_newlines = None

    def run(self, **args):
        """ This will can run simple process """
        for key, value in args.items():
            setattr(self, key, value)

        try:
            cmd = self._cmd.split() if type(self._cmd) is str else self._cmd
            if getattr(self, 'realtime_output'):
                self.stdout=None
            self._cp = subprocess.run(cmd, stdout=self.stdout,
                    stderr=subprocess.PIPE, shell=self.shell, cwd=self.cwd,
                    timeout=self.timeout, env=self.env,
                    universal_newlines=self.universal_newlines)

            self._output = self._cp.stdout
            self._err = self._cp.stderr
            self._returncode = self._cp.returncode

        except TimeoutExpired as e:
            self._err = str(e)
            self._output = ''
            self._returncode = errno.ETIMEDOUT

        except CalledProcessError as e:
            self._err = str(e)
            self._output = ''
            self._returncode = e.returncode

        except Exception as err:
            self._err = "SubProcess Error: " + str(err)
            self._output = ''
            self._returncode = -1

        return self._output, self._err, self._returncode


class PipedProcess(Process):
    """ Execute process with pipe and provide output """

    def __init__(self, cmd):
        super(PipedProcess, self).__init__(cmd)
        self.universal_newlines = None

    def run(self, **args):
        from subprocess import PIPE, Popen

        cmd = self._cmd
        try:
            list_cmds = [x.split() for x in cmd.split(' | ')]
            ps = None
            for index, cmd in enumerate(list_cmds):
                if index == 0:
                    ps = Popen(cmd, stdout=PIPE, universal_newlines=self.universal_newlines)
                else:
                    ps = Popen(cmd, stdin=ps.stdout, stdout=PIPE,
                               stderr=PIPE, universal_newlines=self.universal_newlines)
            if ps is None:
                raise ValueError("No commands given!")
            output = ps.communicate()
            self._output = output[0].strip()
            self._err = output[1].strip()
            self._returncode = ps.returncode
        except Exception as err:
            self._err = "SubProcess Error: " + str(err)
            self._output = ""
            self._returncode = -1
        return self._output, self._err, self._returncode
