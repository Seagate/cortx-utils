import sys
import traceback
from cortx.utils.log import Log
from cortx.utils.cli.errors import ArgumentError

class Terminal:
    
    EMPTY_PASS_FIELD = "Password field can't be empty."
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
            sys.stdout.write('Successfully logged out\n')
        else:
            Log.error(traceback.format_exc())
            sys.stderr('Logout failed\n')

    @staticmethod
    def get_current_password(value):
        """
        Fetches current password for user in non-echo mode.
        :param value:
        :return:
        """
        value = value or getpass(prompt="Current Password: ")
        if not value:
            raise ArgumentError(errno.EINVAL,
                                f"Current {Terminal.EMPTY_PASS_FIELD}")
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
            raise ArgumentError(errno.EINVAL, Terminal.EMPTY_PASS_FIELD)
        if confirm_pass_flag:
            confirm_password = getpass(prompt="Confirm Password: ")
            if not confirm_password:
                raise ArgumentError(errno.EINVAL,
                                    f"Confirm {Terminal.EMPTY_PASS_FIELD}")
            if not confirm_password == value:
                raise ArgumentError(errno.EINVAL, "Password do not match.")
        return value
