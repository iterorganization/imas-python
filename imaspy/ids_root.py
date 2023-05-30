# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.
"""IDSRoot used to be the main way to interact with IDSs in IMASPy.

Keep this file around until v1.0 to signal alpha users that they need to use
:class:`~imaspy.db_entry.DBEntry` and :class:`~imaspy.ids_factory.IDSFactory` classes
instead.
"""


class IDSRoot:
    """Root of IDS tree. Contains all top-level IDSs"""

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "IDSRoot is removed in IMASPy v0.7.0. "
            "See DBEntry for IDS I/O (put, get, etc.). "
            "See IDSFactory for creating empty IDSs."
        )
