import struct
import numpy as np

import pytest
from xxhash import xxh3_64_digest

import imaspy


@pytest.fixture
def minimal(ids_minimal_types):
    return imaspy.IDSFactory(xml_path=ids_minimal_types).new("minimal")


def test_hash_str0d(minimal):
    s = "Test str_0d hash"
    minimal.str_0d = "Test str_0d hash"
    expected = xxh3_64_digest(s.encode("utf-8"))
    assert expected == b"r\x9d\x8dC.JN\x0e"
    assert imaspy.util.calc_hash(minimal.str_0d) == expected


def test_hash_str1d(minimal):
    l = [
        "Test str_1d hash",
        "Of course, there must be ",
        "multiple entries to test!",
    ]
    minimal.str_1d = l
    hashes = list(map(xxh3_64_digest, l))
    expected = xxh3_64_digest(struct.pack("<Q", len(l)) + b"".join(hashes))
    assert expected == b"\x98\x011\x9dx+\x0e\xc0"
    assert imaspy.util.calc_hash(minimal.str_1d) == expected


def test_hash_int0d(minimal):
    i = 273409
    minimal.int_0d = i
    expected = xxh3_64_digest(struct.pack("<i", i))
    assert expected == b"D\x1an\x8b\xbe\x99\x9a\t"
    assert imaspy.util.calc_hash(minimal.int_0d) == expected


def test_hash_flt0d(minimal):
    f = 3.141592
    minimal.flt_0d = f
    expected = xxh3_64_digest(struct.pack("<d", f))
    assert imaspy.util.calc_hash(minimal.flt_0d) == expected


def test_hash_cpx0d(minimal):
    c = 3.141592 - 2.718281j
    minimal.cpx_0d = c
    expected = xxh3_64_digest(struct.pack("<dd", c.real, c.imag))
    assert expected == b"\x18`\xcek\x82\xa0\x18\x0e"
    assert imaspy.util.calc_hash(minimal.cpx_0d) == expected


@pytest.mark.parametrize("n", [1, 2, 3])
def test_hash_int_nd(minimal, n):
    name = f"int_{n}d"
    arr = np.fromfunction(
        lambda i, j=0, k=0: (i << 16) + (j << 8) + k, (5,) * n, dtype=int
    )
    minimal[name] = arr
    flattened = np.ravel(arr, order="F")
    expected = xxh3_64_digest(
        struct.pack("<B", n)
        + (struct.pack("<Q", 5) * n)
        + b"".join(struct.pack("<i", i) for i in flattened)
    )
    assert imaspy.util.calc_hash(minimal[name]) == expected


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_hash_flt_nd(minimal, n):
    name = f"flt_{n}d"
    arr = np.random.random((5,) * n)
    minimal[name] = arr
    flattened = np.ravel(arr, order="F")
    expected = xxh3_64_digest(
        struct.pack("<B", n)
        + (struct.pack("<Q", 5) * n)
        + b"".join(struct.pack("<d", f) for f in flattened)
    )
    assert imaspy.util.calc_hash(minimal[name]) == expected


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6])
def test_hash_cpx_nd(minimal, n):
    name = f"cpx_{n}d"
    arr = np.random.random((5,) * n) + np.random.random((5,) * n) * 1j
    minimal[name] = arr
    flattened = np.ravel(arr, order="F")
    expected = xxh3_64_digest(
        struct.pack("<B", n)
        + (struct.pack("<Q", 5) * n)
        + b"".join(struct.pack("<dd", c.real, c.imag) for c in flattened)
    )
    assert imaspy.util.calc_hash(minimal[name]) == expected


def test_hash_aos():
    cp = imaspy.IDSFactory("3.39.0").core_profiles()
    assert imaspy.util.calc_hash(cp.profiles_1d) == xxh3_64_digest(b"\0\0\0\0\0\0\0\0")
    cp.profiles_1d.resize(3)
    # Check that the empty struct hashes are as expected
    for p1d in cp.profiles_1d:
        assert imaspy.util.calc_hash(p1d) == xxh3_64_digest(b"")
    assert imaspy.util.calc_hash(cp.profiles_1d) == xxh3_64_digest(
        b"\x03\0\0\0\0\0\0\0" + 3 * xxh3_64_digest(b"")
    )
    # Set some data on the structures
    for p1d in cp.profiles_1d:
        p1d.time = 1.0
    struct_hash = imaspy.util.calc_hash(cp.profiles_1d[0])
    assert struct_hash == imaspy.util.calc_hash(cp.profiles_1d[1])
    assert struct_hash == imaspy.util.calc_hash(cp.profiles_1d[2])
    assert imaspy.util.calc_hash(cp.profiles_1d) == xxh3_64_digest(
        b"\x03\0\0\0\0\0\0\0" + 3 * struct_hash
    )


def test_hash_struct():
    cp = imaspy.IDSFactory("3.39.0").core_profiles()
    assert imaspy.util.calc_hash(cp.code) == xxh3_64_digest(b"")

    cp.code.name = "name"
    expected = xxh3_64_digest(b"name" + xxh3_64_digest(b"name"))
    assert imaspy.util.calc_hash(cp.code) == expected

    cp.code.version = "version"
    expected = xxh3_64_digest(
        b"name" + xxh3_64_digest(b"name") + b"version" + xxh3_64_digest(b"version")
    )
    assert imaspy.util.calc_hash(cp.code) == expected

    cp.code.parameters = "parameters"
    expected = xxh3_64_digest(
        b"name"
        + xxh3_64_digest(b"name")
        + b"parameters"
        + xxh3_64_digest(b"parameters")
        + b"version"
        + xxh3_64_digest(b"version")
    )
    assert imaspy.util.calc_hash(cp.code) == expected


def test_hash_ids_properties():
    cp = imaspy.IDSFactory("3.39.0").core_profiles()
    assert imaspy.util.calc_hash(cp.ids_properties) == xxh3_64_digest(b"")

    cp.ids_properties.version_put.data_dictionary = "dd"
    cp.ids_properties.version_put.access_layer = "al"
    cp.ids_properties.version_put.access_layer_language = "lang"
    # This should be ignored for calculating the hash:
    assert imaspy.util.calc_hash(cp.ids_properties) == xxh3_64_digest(b"")


def test_hash_ids():
    cp = imaspy.IDSFactory().core_profiles()
    cp.ids_properties.homogeneous_time = 1
    cp.ids_properties.comment = "Testing hash function"
    cp.code.name = "IMASPy"
    cp.time = [1.0, 2.0, 3.0, 4.0]
    cp.profiles_1d.resize(4)
    for p1d in cp.profiles_1d:
        p1d.grid.rho_tor_norm = [1.0, 2.0]
        p1d.electrons.temperature = [1e6, 2e6]
    assert imaspy.util.calc_hash(cp.ids_properties) == b"3Fw\xab:w7K"