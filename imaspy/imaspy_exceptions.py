# From https://docs.python.org/3/tutorial/errors.html
# But has been true since Python 2.old
class Error(Exception):
    """Base class for low-level exceptions in IMASPy."""

    pass


class IMASPyError(Error):
    """Base class for high-level exceptions in IMASPy.

    Attributes:
        message: Explanation of why the error was raised
    """

    def __init__(self, message):
        self.message = message
