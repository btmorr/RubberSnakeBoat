from enum import StrEnum
from store import Store
from typing import Dict, List, Union


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
    def __init__(self, op: Op, key: str, value: Union[str, None], term: int):
        self.op = op
        self.key = key
        self.value = value
        self.term = term


class InvalidOperationException(Exception):
    pass


class State:
    store: Store
    role: Role = Role.FOLLOWER
    current_term: int = 0
    voted_for: str = ''
    log: List[Entry] = list()
    commit_index: int = -1
    last_applied: int = -1
    # next and match idx fn not yet implemented
    next_index: Dict[str, int] = dict()
    match_index: Dict[str, int] = dict()

    def apply_entry(self, entry: Entry):
        if entry.op == Op.WRITE:
            if entry.value:
                self.store.upsert(entry.key, entry.value)
            else:
                raise InvalidOperationException(f"Invalid Operation: write missing value for key {entry.key}")
        elif entry.op == Op.DELETE:
            self.store.delete(entry.key)
        else:
            raise InvalidOperationException(f"Invalid Operation: {entry.op}")

    def apply_entries(self, entries: List[Entry]):
        [self.apply_entry(en) for en in entries]

    def append_entries(
            self,
            term: int,
            leader_id: int,  # noqa -- to be used
            prev_log_index: int,
            prev_log_term: int,
            entries: List[Entry],
            leader_commit: int
    ) -> AppendResult:
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
            self.apply_entries(self.log[self.last_applied + 1:self.commit_index + 1])
        return AppendResult(self.current_term, True)
