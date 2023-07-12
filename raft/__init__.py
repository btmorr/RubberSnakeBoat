from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Union


class Role(Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


class Op(Enum):
    READ = 0
    WRITE = 1
    DELETE = 2


class LogEntry(BaseModel):
    op: Op
    key: str
    value: Union[str, None]
    term: int


class AppendEntries(BaseModel):
    term: int
    leaderId: int
    prevLogIndex: int
    prevLogTerm: int
    entries: List[LogEntry] = list()
    leaderCommit: int


class AppendEntriesResponse(BaseModel):
    term: int
    success: bool


class State:
    role: Role = Role.FOLLOWER
    currentTerm: int = 0
    votedFor: int
    log: List[LogEntry] = list()
    commitIndex: int = -1
    # application not yet implemented
    lastApplied: int = -1
    # next and match idx fn not yet implemented
    nextIndex: Dict[str, int] = dict()
    matchIndex: Dict[str, int] = dict()

    def append_entries_receiver(self, ae: AppendEntries) -> AppendEntriesResponse:
        if ae.term < self.currentTerm:
            # ae from expired leader
            return AppendEntriesResponse(term=self.currentTerm, success=False)
        if ae.term > self.currentTerm:
            # election happened, become follower
            self.currentTerm = ae.term
            self.role = Role.FOLLOWER
        if ae.prevLogIndex == -1:
            # only before any logs have been shipped
            self.log.extend(ae.entries)
            return AppendEntriesResponse(term=self.currentTerm, success=True)
        try:
            self.log[ae.prevLogIndex]
        except IndexError:
            # previous entry missing
            success = False
        else:
            success = True
        if len(self.log) > ae.prevLogIndex:
            self.log = self.log[:ae.prevLogIndex+1]
            self.log.extend(ae.entries)
        if ae.leaderCommit > self.commitIndex:
            self.commitIndex = min(ae.leaderCommit, len(self.log))
        return AppendEntriesResponse(term=self.currentTerm, success=success)
