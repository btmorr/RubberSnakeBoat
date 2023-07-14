import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from fastapi.testclient import TestClient  # noqa
from server import build_app  # noqa
from raft import State, Role


def test_store_read_empty():
    app = build_app()

    client = TestClient(app)
    response = client.get("/?key=this")
    assert response.status_code == 404


def test_store_write():
    state = State()
    app = build_app(state)
    # node must be leader to accept writes
    state.role = Role.LEADER

    client = TestClient(app)
    response = client.post("/?key=this&value=that")
    assert response.status_code == 201


def test_store_read_after_write():
    state = State()
    app = build_app(state)
    # node must be leader to accept writes
    state.role = Role.LEADER

    client = TestClient(app)
    client.post("/?key=this&value=that")
    response = client.get("/?key=this")
    assert response.status_code == 200
    assert response.json()["value"] == 'that'


def test_delete():
    state = State()
    app = build_app(state)
    # node must be leader to accept writes
    state.role = Role.LEADER

    client = TestClient(app)
    response = client.delete("/?key=this")
    assert response.status_code == 204


def test_write_follower():
    app = build_app()
    # state defaults to follower, and should reject writes

    client = TestClient(app)
    response = client.post("/?key=this&value=that", follow_redirects=False)
    assert response.status_code == 308
    response = client.delete("/?key=this", follow_redirects=False)
    assert response.status_code == 308
