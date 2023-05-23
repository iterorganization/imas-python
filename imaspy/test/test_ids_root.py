from imaspy.ids_root import IDSRoot


def test_root_init():
    IDSRoot()


def test_stringify():
    root = IDSRoot()
    str(root)
