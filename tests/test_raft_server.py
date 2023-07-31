import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from fastapi.testclient import TestClient  # noqa
from server import build_app  # noqa
from raft import State  # noqa
from store import Store  # noqa


def test_rpc_append_entries():
    """this corresponds to `test_append_entries_empty` --
    see that file for comprehensive test cases on the append handler

    this test is sufficient to guarantee the duck-typing assumption for the
    append endpoint"""
    app = build_app()

    client = TestClient(app)

    body = {
            "term": 1,
            "leader_id": 'localhost:5000',
            "prev_log_index": -1,
            "prev_log_term": 0,
            "entries": [],
            "leader_commit": -1
    }
    res = client.post("/rpc/append", json=body)
    assert res.status_code == 200
    assert res.json()["success"]


def test_rpc_request_vote():
    """this corresponds to `test_request_vote_initial` --
    see that file for comprehensive test cases on the vote handler

    this test is sufficient to guarantee the duck-typing assumption for the
    vote endpoint"""
    state = State(Store())
    state.address = 'localhost:1010'
    app = build_app(state)

    client = TestClient(app)

    test_term = 1
    body = {
        "term": test_term,
        "candidate_id": 'localhost:5000',
        "last_log_index": -1,
        "last_log_term": 0,
    }
    res = client.post("/rpc/vote", json=body)
    assert res.status_code == 200
    assert res.json()["vote_granted"]
    assert res.json()["term"] == test_term
