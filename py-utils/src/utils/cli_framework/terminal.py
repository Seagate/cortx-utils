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

import sys
import traceback
from cortx.utils.log import Log
from cortx.utils.cli_framework.errors import CliError
from getpass import getpass
import errno

class Terminal:
    """
    Class to show prompts on consol for purpose of information,
    waring or to get inputs from user or confirmation messages
    """

    @staticmethod
    def get_quest_answer(name: str) -> bool:
        """
        Asks user user a question using stdout
        Returns True or False, depending on an answer

        :param quest: question string
        :return: True or False depending on user input
        """

        while True:
            # Postive answer is default
            sys.stdout.write(f'Are you sure you want to perform "{name}" command? [Y/n] ')

            usr_input = input().lower()
            if usr_input in ['y', 'yes', '']:
                return True
            elif usr_input in ['n', 'no']:
                return False
            else:
                sys.stdout.write("Please answer with 'yes' or 'no'\n")

    @staticmethod
    def logout_alert(is_logged_out: bool):
        if is_logged_out:
            sys.stdout.write("Successfully logged out\n")
        else:
            Log.error(traceback.format_exc())
            sys.stderr("Logout failed\n")

    @staticmethod
    def get_current_password(value):
        """
        Fetches current password for user in non-echo mode.
        :param value:
        :return:
        """
        value = value or getpass(prompt="Current Password: ")
        if not value:
            raise CliError(errno.EINVAL,
                            "Could not obtain current password")
        return value

    @staticmethod
    def get_password(value, confirm_pass_flag=True):
        """
        Fetches the Password from Terminal in Non-Echo Mode.
        :return:
        """
        sys.stdout.write(("\nPassword must contain the following.\n1) 1 upper and lower "
        "case character.\n2) 1 numeric character.\n3) 1 of the !@#$%^&*()_+-=[]{}|' "
                          "characters.\n"))
        value = value or getpass(prompt="Password: ")
        if not value:
            raise CliError(errno.EINVAL, "Password field can not be empty.")
        if confirm_pass_flag:
            confirm_password = getpass(prompt="Confirm Password: ")
            if not confirm_password:
                raise CliError(errno.EINVAL,
                            "Could not obtain confirm password")
            if not confirm_password == value:
                raise CliError(errno.EINVAL, "Password do not match.")
        return value
