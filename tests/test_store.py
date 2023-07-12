import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from store import Store  # noqa


def test_read_empty():
    s = Store()
    assert(not s.read('empty'))


def test_read_after_write():
    s = Store()
    key = 'this'
    value = 'that'
    s.upsert(key, value)
    assert(s.read(key) == value)


def test_read_after_overwrite():
    s = Store()
    key = 'this'
    value1 = 'that'
    value2 = 'other'
    s.upsert(key, value1)
    s.upsert(key, value2)
    assert (s.read(key) == value2)


def test_read_after_delete():
    s = Store()
    key = 'this'
    value = 'that'
    s.upsert(key, value)
    s.delete(key)
    assert(not s.read(key))
