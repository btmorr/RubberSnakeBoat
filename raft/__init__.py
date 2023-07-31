from enum import StrEnum
import os
from store import Store
from typing import Dict, List


class Role(StrEnum):
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


class Op(StrEnum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"


class AppendResult:
    def __init__(self, term: int, success: bool):
        self.term = term
        self.success = success


class Entry:
    """This class must match the server.LogEntry class"""
    def __init__(self, op: Op, key: str, value: str | None, term: int):
        self.op = op
        self.key = key
        self.value = value
        self.term = term


class InvalidOperationException(Exception):
    pass


class ForeignNode:
    # todo: add client connection
    next_index: int = 0
    match_index: int = -1


class State:
    def __init__(self, store: Store):
        self.store = store
        self.address = os.environ.get('RSB_ADDRESS', 'testing')
        if self.address == 'testing':
            print("Warning! RSB_ADDRESS not found, defaulting to test mode")

        self.foreign_nodes: Dict[str, ForeignNode] = dict()
        nodes_raw = os.environ.get('RSB_NODES', '')
        for n in nodes_raw.split(','):
            if n != self.address:
                self.foreign_nodes[n] = ForeignNode()

        # -- volatile state --
        self.role: Role = Role.FOLLOWER
        self.commit_index = -1
        self.last_applied = -1
        self.next_index: Dict[str, int] = dict()
        self.match_index: Dict[str, int] = dict()

        # -- non-volatile state (write to disk before confirming update) --
        self.log: List[Entry] = list()
        self.current_term: int = 0
        self.voted_for: str = ''

    def _apply_entry(self, entry: Entry):
        """This method takes an entry that should be committed to the state
        of the data store, and performs the specified transformation of that
        state. It should not be called directly, but only under the call chain
        of the handler that is responsible for accepting commit ops from the
        leader node, or the task that decides entries are ready to commit, if
        this node is the leader."""
        if entry.op == Op.WRITE:
            if entry.value:
                self.store.upsert(entry.key, entry.value)
            else:
                raise InvalidOperationException(
                    f"Invalid Entry: write missing value for key {entry.key}")
        elif entry.op == Op.DELETE:
            self.store.delete(entry.key)
        else:
            raise InvalidOperationException(f"Invalid Operation: {entry.op}")

    def _apply_entries(self, entries: List[Entry]):
        """This method takes a list of entries that should be committed to the
        state of the data store, and performs the specified transformation of
        that state. It should not be called directly, but only under the call
        chain of the handler that is responsible for accepting commit ops from
        the leader node, or the task that decides entries are ready to commit,
        if this node is the leader."""
        [self._apply_entry(en) for en in entries]

    def append_entries(
            self,
            term: int,
            leader_id: int,  # noqa -- to be used
            prev_log_index: int,
            prev_log_term: int,
            entries: List[Entry],
            leader_commit: int
    ) -> AppendResult:
        """Performs various tasks needed to ensure consistent state of both the
        data store and also of the node leader election process and log
        shipping behavior. This endpoint is complex by necessity. See the
        'AppendEntriesRPC' and 'Rules for Servers' sections of the raft paper.
        """
        if term < self.current_term:
            # ae from expired leader
            return AppendResult(self.current_term, False)
        if term > self.current_term:
            # election happened, become follower
            self.current_term = term
            self.role = Role.FOLLOWER
        if prev_log_index == -1:
            # only before any logs have been shipped
            self.log.extend(entries)
            return AppendResult(self.current_term, True)
        try:
            prev_log = self.log[prev_log_index]
        except IndexError:
            # previous entry missing
            return AppendResult(self.current_term, False)
        else:
            # entry found, check term
            if prev_log.term != prev_log_term:
                # drop mismatched log
                self.log = self.log[:prev_log_index]
                return AppendResult(self.current_term, False)
        if len(self.log) > prev_log_index:
            # drop logs past previous known index
            self.log = self.log[:prev_log_index+1]
            self.log.extend(entries)
        if leader_commit > self.commit_index:
            self.commit_index = min(leader_commit, len(self.log))
        if self.commit_index > self.last_applied:
            self._apply_entries(
                self.log[self.last_applied + 1:self.commit_index + 1])
        return AppendResult(self.current_term, True)
