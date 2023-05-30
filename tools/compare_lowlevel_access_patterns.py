"""Compare the access patterns of the lowlevel UAL API between IMASPy and the HLI.
"""

from functools import wraps
from pathlib import Path
import sys
import traceback

import click

import imas
import imaspy
from imaspy.test.test_helpers import fill_with_random_data
from imaspy.ids_defs import IDS_TIME_MODE_HETEROGENEOUS


class UALWrapper:
    def __init__(self, ual_module):
        self._ual = ual_module
        self._log = []

    def __getattr__(self, name):
        value = getattr(self._ual, name)
        if callable(value):

            @wraps(value)
            def wrapper(*args, **kwargs):
                self._log.append((name, str(args), str(kwargs)))
                return value(*args, **kwargs)

            return wrapper
        return value


# Monkeypatch _ual_lowlevel
wrapper = UALWrapper(sys.modules["imas._ual_lowlevel"])
imas._ual_lowlevel = wrapper
for item in sys.modules:
    if item.startswith("imas") and item.endswith("._ual_lowlevel"):
        sys.modules[item] = wrapper
# And the imported locals in all imas modules
for item in sys.modules:
    if item.startswith("imas"):
        for alias in "_ual_lowlevel", "ull":
            if hasattr(sys.modules[item], alias):
                setattr(sys.modules[item], alias, wrapper)


def compare_ids_put(imaspy_ids, hli_ids):
    imas._ual_lowlevel._log.clear()
    # Start with hli IDS
    dbentry = imas.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "ITER", 1, 1, "test")
    dbentry.create()
    try:
        dbentry.put(hli_ids)
    except Exception as exc:
        print("Caught error while putting hli ids:", exc)
        traceback.print_exc()
    dbentry.close()
    hli_log = imas._ual_lowlevel._log
    imas._ual_lowlevel._log = []
    # And then the imaspy IDS
    dbentry = imaspy.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "ITER", 1, 1, "test")
    dbentry.create()
    try:
        dbentry.put(imaspy_ids)
    except Exception as exc:
        print("Caught error while putting imaspy ids:", exc)
        traceback.print_exc()
    dbentry.close()
    imaspy_log = imas._ual_lowlevel._log
    imas._ual_lowlevel._log = []
    hli_log_text = "\n".join("\t".join(item) for item in hli_log)
    imaspy_log_text = "\n".join("\t".join(item) for item in imaspy_log)
    Path("/tmp/hli.log").write_text(hli_log_text)
    Path("/tmp/imaspy.log").write_text(imaspy_log_text)
    print("Logs stored in /tmp/hli.log and /tmp/imaspy.log")


def compare_ids_get(imaspy_ids):
    # First put the ids
    idbentry = imaspy.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "ITER", 1, 1, "test")
    idbentry.create()
    idbentry.put(imaspy_ids)

    dbentry = imas.DBEntry(imaspy.ids_defs.MEMORY_BACKEND, "ITER", 1, 1, "test")
    dbentry.open()
    # Start with hli IDS
    imas._ual_lowlevel._log.clear()
    dbentry.get(imaspy_ids.metadata.name)
    hli_log = imas._ual_lowlevel._log
    imas._ual_lowlevel._log = []
    # And then the imaspy IDS
    idbentry.get(imaspy_ids.metadata.name)
    imaspy_log = imas._ual_lowlevel._log
    imas._ual_lowlevel._log = []
    # Cleanup
    dbentry.close()
    idbentry.close()
    hli_log_text = "\n".join("\t".join(item) for item in hli_log)
    imaspy_log_text = "\n".join("\t".join(item) for item in imaspy_log)
    Path("/tmp/hli.log").write_text(hli_log_text)
    Path("/tmp/imaspy.log").write_text(imaspy_log_text)
    print("Logs stored in /tmp/hli.log and /tmp/imaspy.log")


@click.command()
@click.argument("ids_name")
@click.argument("method", type=click.Choice(["put", "get"]))
@click.option(
    "--heterogeneous",
    is_flag=True,
    help="Use heterogeneous time mode instead of homogeneous time.",
)
def main(ids_name, method, heterogeneous):
    """Compare lowlevel calls done by IMASPy vs. the Python HLI

    This program fills the provided IDS with random data, then does I/O with it using
    both the Python HLI and the IMASPy APIs. The resulting calls to the lowlevel Access
    Layer are logged to respectively /tmp/hli.log and /tmp/imaspy.log.

    You may use your favorite diff tool to compare the two files.

    \b
    IDS_NAME:   The name of the IDS to use for testing, for example "core_profiles".
    """
    imaspy_ids = imaspy.IDSFactory().new(ids_name)
    hli_ids = getattr(imas, ids_name)()

    fill_with_random_data(imaspy_ids)
    hli_ids.deserialize(imaspy_ids.serialize())

    if heterogeneous:
        # Change time mode
        time_mode = IDS_TIME_MODE_HETEROGENEOUS
        imaspy_ids.ids_properties.homogeneous_time = time_mode
        hli_ids.ids_properties.homogeneous_time = time_mode

    if method == "put":
        compare_ids_put(imaspy_ids, hli_ids)
    elif method == "get":
        compare_ids_get(imaspy_ids)


if __name__ == "__main__":
    main()
