from cortx.utils.cli_framework.errors import CliError
import errno


class ArgType:

    def validate(self, val):
       raise CliError(errno.ENOSYS, "validate not implemented")

class IntType(ArgType):

    @staticmethod
    def validate(value):
        try:
            if int(value) > -1:
                return int(value)
            raise CliError(errno.EINVAL, "Value Must be Positive Integer")
        except ValueError:
            raise CliError(errno.EINVAL,"Invalid argument.")
