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