import pytest

from imaspy.ids_root import IDSRoot

def test_root_init():
    root = IDSRoot()


def test_stringify():
    root = IDSRoot()
    str(root)
