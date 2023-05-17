# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

""" Exception specific for access layers"""


class ALException(Exception):
    def __init__(self, message, errorStatus=None):
        if errorStatus is not None:
            Exception.__init__(self, message + "\nError status=" + str(errorStatus))
        else:
            Exception.__init__(self, message)
