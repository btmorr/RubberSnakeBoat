import os
import sys

import pytest

sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from raft import State, Entry, Op, Role, InvalidOperationException  # noqa
from store import Store  # noqa


def test_append_entries_empty():
    """test initial heartbeat condition, e.g.: successful election but no log
    entries"""
    term = 1
    s = State(Store())
    # simulate a previous successful election
    s.current_term = term

    res = s.append_entries(
        term=term,
        leader_id=0,
        prev_log_index=-1,
        prev_log_term=0,
        entries=list(),
        leader_commit=-1)
    assert res.success
    assert res.term == term


def test_append_entries_nonempty_first():
    """test initial non-empty heartbeat condition, e.g.: successful election
    but no previous log entries, first non-empty append"""
    term = 1
    # simulate a previous successful election
    s = State(Store())
    s.current_term = term

    le = Entry(op=Op.WRITE, key='this', value='that', term=term)

    res = s.append_entries(
        term=term,
        leader_id=0,
        prev_log_index=-1,
        prev_log_term=0,
        entries=[le],
        leader_commit=-1)
    assert res.success
    assert res.term == term
    assert len(s.log) == 1
    assert s.log[0].term == term
    assert s.log[0].op == le.op


def test_append_entries_nonempty():
    """test non-empty heartbeat condition, e.g.: successful election and
    previous log entries, subsequent non-empty append, same term"""
    term = 1
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=term)
    # simulate a previous successful election and write
    s = State(Store())
    s.current_term = term
    s.log = [le0]

    le1 = Entry(op=Op.DELETE, key='this', value=None, term=term)

    res = s.append_entries(
        term=term,
        leader_id=0,
        prev_log_index=0,
        prev_log_term=1,
        entries=[le1],
        leader_commit=0)
    assert res.success
    assert res.term == term
    assert len(s.log) == 2
    assert s.log[0].term == term
    assert s.log[0].op == le0.op
    assert s.log[1].term == term
    assert s.log[1].op == le1.op
    assert s.commit_index == 0


def test_append_entries_evict():
    """test non-empty heartbeat condition for new term, evicting at least one
    uncommitted entry from prior term"""
    term = 1
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=term)
    le1 = Entry(op=Op.DELETE, key='this', value=None, term=term)
    # simulate a previous successful election and write
    s = State(Store())
    s.current_term = term
    s.log = [le0, le1]

    new_term = term + 1
    le2 = Entry(op=Op.WRITE, key='this', value='other', term=new_term)

    # commit index 0 and expect a record from term 2 at index 1
    res = s.append_entries(
        term=new_term,
        leader_id=0,
        prev_log_index=1,
        prev_log_term=2,
        entries=[le2],
        leader_commit=0)
    # expect non-success response indicating that new leader should
    # retry ship with an earlier payload to replace evicted record
    assert not res.success
    assert res.term == new_term
    # expect follower to evict logs
    assert len(s.log) == 1
    assert s.log[0].term == term
    # expect follower to truncate log
    assert s.log[0].op == le0.op
    # expect follower to not commit, since log is incomplete
    assert s.commit_index == -1


def test_append_entries_nonempty_missing():
    """test missing prevLogIndex"""
    term = 1
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=term)
    # simulate a previous successful election and write
    s = State(Store())
    s.current_term = term
    s.log = [le0]

    le1 = Entry(op=Op.DELETE, key='this', value=None, term=term)

    res = s.append_entries(
        term=term,
        leader_id=0,
        prev_log_index=1,
        prev_log_term=1,
        entries=[le1],
        leader_commit=0)
    assert not res.success
    assert res.term == term
    assert len(s.log) == 1
    # expect follower to not commit, since log is incomplete
    assert s.commit_index == -1


def test_append_entries_nonempty_discard():
    """test discarding an uncommitted entry from a past term"""
    term = 1
    new_term = 2
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=term)
    le1 = Entry(op=Op.DELETE, key='this', value=None, term=term)
    # simulate a previous successful election and write
    s = State(Store())
    s.current_term = term
    s.log = [le0, le1]
    s.commit_index = 0
    s.last_applied = 0

    # This should become the second log entry, replacing le1
    le2 = Entry(op=Op.WRITE, key='this', value='other', term=term)

    res = s.append_entries(
        term=new_term,
        leader_id=0,
        prev_log_index=0,
        prev_log_term=1,
        entries=[le2],
        leader_commit=0)
    assert res.success
    assert res.term == new_term
    assert len(s.log) == 2
    assert s.log[1].op == le2.op
    assert s.log[1].value == le2.value
    assert s.commit_index == 0


def test_append_entries_invalid_term():
    """test non-empty heartbeat condition with expired term"""
    term = 2
    past_term = term-1
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=past_term)
    # simulate a previous successful election and write
    s = State(Store())
    s.current_term = term
    s.log = [le0]

    le1 = Entry(op=Op.DELETE, key='this', value=None, term=past_term)

    res = s.append_entries(
        term=past_term,
        leader_id=0,
        prev_log_index=0,
        prev_log_term=past_term,
        entries=[le1],
        leader_commit=0)
    assert not res.success
    assert res.term == term
    assert len(s.log) == 1
    assert s.log[0].term == le0.term
    assert s.log[0].op == le0.op
    assert s.commit_index == -1


def test_append_entries_new_term():
    """test initial heartbeat condition, e.g.: successful election but no log
    entries"""
    term = 1
    new_term = term + 1
    s = State(Store())
    # simulate a previous successful election
    s.current_term = term
    s.role = Role.LEADER

    res = s.append_entries(
        term=new_term,
        leader_id=0,
        prev_log_index=-1,
        prev_log_term=0,
        entries=list(),
        leader_commit=-1)
    assert res.success
    assert res.term == new_term
    assert s.role == Role.FOLLOWER
    assert s.current_term == new_term


def test_append_entries_apply_writes():
    """test committing entries"""
    term = 1
    k1 = 'this'
    v1 = 'that'
    k2 = 'hem'
    v2 = 'haw'
    le0 = Entry(op=Op.WRITE, key=k1, value=v1, term=term)
    le1 = Entry(op=Op.WRITE, key=k2, value=v2, term=term)
    # simulate a previous successful election and write
    s = State(Store())
    s.current_term = term
    s.log = [le0, le1]

    # no new entries, commit existing
    res = s.append_entries(
        term=term,
        leader_id=0,
        prev_log_index=1,
        prev_log_term=term,
        entries=[],
        leader_commit=1)
    assert res.success
    assert s.commit_index == 1
    assert s.store.read(k1) == v1
    assert s.store.read(k2) == v2


def test_append_entries_apply_delete():
    """test committing entries"""
    term = 1
    k = 'this'
    v = 'that'
    le0 = Entry(op=Op.WRITE, key=k, value=v, term=term)
    le1 = Entry(op=Op.DELETE, key=k, value=None, term=term)
    # simulate a previous successful election and write
    s = State(Store())
    s.current_term = term
    s.log = [le0, le1]

    # no new entries, commit existing
    res = s.append_entries(
        term=term,
        leader_id=0,
        prev_log_index=1,
        prev_log_term=term,
        entries=[],
        leader_commit=1)
    assert res.success
    assert len(s.log) == 2
    assert s.commit_index == 1
    assert not s.store.read(k)


def test_invalid_entry_operation():
    s = State(Store())

    ie0 = Entry(op=Op.READ, key='this', value='that', term=1)
    with pytest.raises(InvalidOperationException):
        s.apply_entry(ie0)


def test_invalid_entry_value():
    s = State(Store())

    ie0 = Entry(op=Op.WRITE, key='this', value=None, term=1)
    with pytest.raises(InvalidOperationException):
        s.apply_entry(ie0)


def test_environment_init():
    node_addr = 'localhost:12345'
    os.environ['RSB_ADDRESS'] = node_addr
    os.environ['RSB_NODES'] = f'{node_addr},localhost:1010,localhost:123456'

    s = State(Store())
    assert s.address == node_addr
    assert len(s.foreign_nodes.keys()) == 2
