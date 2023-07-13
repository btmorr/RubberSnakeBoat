from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
from store import Store
from raft import Entry, State, Op


# all FastAPI and Pydantic code should be limited to the server module
class ReadResponse(BaseModel):
    value: Union[str, None]


class LogEntry(BaseModel):
    op: Op
    key: str
    value: Union[str, None]
    term: int

    def as_entry(self) -> Entry:
        """
        re-serialization to prevent leaking pydantic model into internal code,
        may be technically unnecessary due to duck-typing, but this can be used
        to satisfy the type-checker by doing something along the lines of
        [le.as_entry() for le in log_entries]
        """
        return Entry(self.op, self.key, self.value, self.term)


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


def build_app():
    app = FastAPI()
    store = Store()
    state = State()

    # ----- DB Router -----
    @app.get("/")
    async def db_get(key: str) -> ReadResponse:
        """reads the specified value"""
        v = store.read(key)
        if not v:
            raise HTTPException(status_code=404, detail="Not found")
        return ReadResponse(value=v)

    @app.post("/", status_code=201)
    async def db_upsert(key: str, value: str):
        """inserts the specified value without checking for previous existence"""
        store.upsert(key, value)

    @app.delete("/", status_code=204)
    async def db_delete(key: str):
        """deletes specified key without checking for existence"""
        store.delete(key)

    # ----- Raft Router -----
    @app.post("/rpc/append")
    async def rpc_append_entries(req: AppendEntries) -> AppendEntriesResponse:
        """handles AppendEntry RPC requests for writes and heartbeats"""
        res = state.append_entries(
            term=req.term,
            leader_id=req.leaderId,
            prev_log_index=req.prevLogIndex,
            prev_log_term=req.prevLogTerm,
            entries=req.entries,  # noqa  -- see note in LogEntry.as_entry
            leader_commit=req.leaderCommit)
        return AppendEntriesResponse(term=res.term, success=res.success)

    return app
