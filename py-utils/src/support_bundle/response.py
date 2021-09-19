class Response(object):
    """ Represents a response after processing of a request """

    def __init__(self, status, output=''):
        """ Initializes Response attributes."""
        self._status = str(status)
        self._output = str(output)

    def output(self):
        return self._output

    def status(self):
        return self._status

    def __str__(self):
        return '%s: %s' % (self._status, self._output)
