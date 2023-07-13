import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from fastapi.testclient import TestClient  # noqa
from server import build_app  # noqa


def test_rpc_append_entries():
    """this corresponds to test_append_entries_empty in test_raft.py --
    see that file for comprehensive test cases on the append handler"""
    app = build_app()

    client = TestClient(app)

    body = {
            "term": 1,
            "leaderId": 0,
            "prevLogIndex": -1,
            "prevLogTerm": 0,
            "leaderCommit": -1
    }
    res = client.post("/rpc/append", json=body)
    assert res.status_code == 200
    assert res.json()["success"]
