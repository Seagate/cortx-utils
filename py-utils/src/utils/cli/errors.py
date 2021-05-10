
import argparse

class ArgumentError(argparse.ArgumentError):
    def __init__(self, rc, message, argument=None):
        super(ArgumentError, self).__init__(argument, message)
        self.rc = rc
        self.message = message

    def __str__(self):
        return f"{self.rc}: {self.message}"
