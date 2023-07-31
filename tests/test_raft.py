import os
import sys

sys.path.append(os.path.realpath(os.path.dirname(__file__)+"/.."))

from raft import State, SINGLE_NODE_DEPLOYMENT  # noqa
from store import Store  # noqa


def test_environment_empty():
    s = State(Store())
    assert s.address == SINGLE_NODE_DEPLOYMENT


def test_environment_init():
    node_addr = 'localhost:12345'
    os.environ['RSB_ADDRESS'] = node_addr
    os.environ['RSB_NODES'] = f'{node_addr},localhost:1010,localhost:123456'

    s = State(Store())
    assert s.address == node_addr
    assert len(s.foreign_nodes.keys()) == 2

    os.environ.pop('RSB_ADDRESS')
    os.environ.pop('RSB_NODES')
