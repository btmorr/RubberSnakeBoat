from enum import Enum
from typing import Dict, List, Union


class Role(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


class Op(Enum):
    READ = 0
    WRITE = 1
    DELETE = 2


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


class State:
    role: Role = Role.FOLLOWER
    currentTerm: int = 0
    votedFor: int
    log: List[Entry] = list()
    commitIndex: int = -1
    # application not yet implemented
    lastApplied: int = -1
    # next and match idx fn not yet implemented
    nextIndex: Dict[str, int] = dict()
    matchIndex: Dict[str, int] = dict()

    def append_entries(
            self,
            term: int,
            leader_id: int,  # noqa -- to be used
            prev_log_index: int,
            prev_log_term: int,
            entries: List[Entry],
            leader_commit: int) -> AppendResult:
        if term < self.currentTerm:
            # ae from expired leader
            return AppendResult(self.currentTerm, False)
        if term > self.currentTerm:
            # election happened, become follower
            self.currentTerm = term
            self.role = Role.FOLLOWER
        if prev_log_index == -1:
            # only before any logs have been shipped
            self.log.extend(entries)
            return AppendResult(self.currentTerm, True)
        try:
            prev_log = self.log[prev_log_index]
        except IndexError:
            # previous entry missing
            success = False
        else:
            # entry found, check term
            success = prev_log.term == prev_log_term
            if not success:
                self.log = self.log[:prev_log_index + 1]
        if len(self.log) > prev_log_index:
            self.log = self.log[:prev_log_index+1]
            self.log.extend(entries)
        if leader_commit > self.commitIndex:
            self.commitIndex = min(leader_commit, len(self.log))
        return AppendResult(self.currentTerm, success)
