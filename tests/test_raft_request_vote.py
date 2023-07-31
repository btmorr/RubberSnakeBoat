import os
import sys

sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from raft import State, Role, Entry, Op  # noqa
from store import Store  # noqa


def test_request_vote_initial():
    s = State(Store())
    s.address = 'localhost:1010'

    test_term = 1
    test_addr = 'localhost:5000'
    res = s.request_vote(
        term=test_term,
        candidate_id=test_addr,
        last_log_index=-1,
        last_log_term=0)
    assert res.vote_granted
    assert res.term == test_term
    assert s.voted_for == test_addr


def test_request_vote_successive():
    s = State(Store())
    s.address = 'localhost:1010'
    s.term = 5
    s.voted_for = s.address
    s.role = Role.LEADER

    test_term = s.term + 1
    test_addr = 'localhost:5000'
    res = s.request_vote(
        term=test_term,
        candidate_id=test_addr,
        last_log_index=-1,
        last_log_term=0)
    assert res.vote_granted
    assert res.term == test_term
    assert s.voted_for == test_addr
    assert s.role == Role.FOLLOWER


def test_request_vote_incorrect_last_log_index():
    test_term = 1
    s = State(Store())
    s.address = 'localhost:1010'
    s.voted_for = s.address
    s.role = Role.LEADER
    s.current_term = test_term
    le = Entry(op=Op.WRITE, key='this', value='that', term=test_term)
    s.log = [le]

    test_addr = 'localhost:5000'
    res = s.request_vote(
        term=test_term+1,
        candidate_id=test_addr,
        last_log_index=-1,
        last_log_term=0)
    assert not res.vote_granted
    assert res.term == test_term
    assert s.voted_for == s.address
    assert s.role == Role.LEADER


def test_request_vote_incorrect_last_log_term():
    test_term = 2
    s = State(Store())
    s.address = 'localhost:1010'
    s.voted_for = s.address
    s.role = Role.LEADER
    s.current_term = test_term
    le = Entry(op=Op.WRITE, key='this', value='that', term=test_term)
    s.log = [le]

    test_addr = 'localhost:5000'
    res = s.request_vote(
        term=test_term+1,
        candidate_id=test_addr,
        last_log_index=0,
        last_log_term=test_term-1)
    assert not res.vote_granted
    assert res.term == test_term
    assert s.voted_for == s.address
    assert s.role == Role.LEADER

