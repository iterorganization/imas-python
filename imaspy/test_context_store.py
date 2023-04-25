import pytest

from imaspy.context_store import ContextStore, ContextError

def test_contextstore_init():
    store = ContextStore()
    assert isinstance(store, ContextStore)

def test_contexterror_init():
    with pytest.raises(ContextError) as exc_info:
        raise ContextError("A test message")
    assert exc_info.type is ContextError
    assert exc_info.value.args[0] == "A test message"

def test_strip_path():
    store = ContextStore()
    store[1] = "/"
    stripped_path = store.strip_context("/pulse_schedule", 1)
    assert stripped_path == "pulse_schedule"

def test_strip_unrelated_path():
    store = ContextStore()
    store[2] = '/pulse_schedule'
    with pytest.raises(ContextError):
        stripped_path = store.strip_context("/gyrokinetics", 2)
