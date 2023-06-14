import pytest

from imaspy.exception import ValidationError


@pytest.mark.parametrize(
    "msg, aos_indices, expected",
    [
        ("test(itime)/x", {"itime": 1}, "test[1].x"),
        ("test(i1)/(i2)/itime", {"i1": 1, "i2": 2, "itime": 3}, "test[1].[2].itime"),
        ("test(i1) remove i1", {"i1": 1}, "test remove i1"),
        ("test(:) remove", {}, "test remove"),
        ("test(:,:) remove", {}, "test remove"),
        ("test(:,:,:,:) remove", {}, "test remove"),
    ],
)
def test_validation_error_path_replacement(msg, aos_indices, expected):
    assert ValidationError(msg, aos_indices).args[0] == expected
