import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from raft import *  # noqa


def test_append_entries_empty():
    """test initial heartbeat condition, e.g.: successful election but no log
    entries"""
    term = 1
    s = State()
    # simulate a previous successful election
    s.currentTerm = term

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
    s = State()
    s.currentTerm = term

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
    s = State()
    s.currentTerm = term
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
    assert s.commitIndex == 0


def test_append_entries_nonempty_missing():
    """test missing prevLogIndex"""
    term = 1
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=term)
    # simulate a previous successful election and write
    s = State()
    s.currentTerm = term
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
    assert s.commitIndex == 0


def test_append_entries_nonempty_discard():
    """test discarding an uncommitted entry from a past term"""
    term = 1
    new_term = 2
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=term)
    le1 = Entry(op=Op.DELETE, key='this', value=None, term=term)
    # simulate a previous successful election and write
    s = State()
    s.currentTerm = term
    s.log = [le0, le1]
    s.commitIndex = 0
    s.lastApplied = 0

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
    assert s.commitIndex == 0


def test_append_entries_invalid_term():
    """test non-empty heartbeat condition with expired term"""
    term = 2
    past_term = term-1
    le0 = Entry(op=Op.WRITE, key='this', value='that', term=past_term)
    # simulate a previous successful election and write
    s = State()
    s.currentTerm = term
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
    assert s.commitIndex == -1


def test_append_entries_new_term():
    """test initial heartbeat condition, e.g.: successful election but no log
    entries"""
    term = 1
    new_term = term + 1
    s = State()
    # simulate a previous successful election
    s.currentTerm = term
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
    assert s.currentTerm == new_term
