from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
from store import Store
from raft import State, Op


# all FastAPI and Pydantic code should be limited to the server module
# (this might have to be flexed for BackgroundTasks depending on performance)
class ReadResponse(BaseModel):
    value: Union[str, None]


class LogEntry(BaseModel):
    op: Op
    key: str
    value: Union[str, None]
    term: int


class AppendEntries(BaseModel):
    term: int
    leader_id: int
    prev_log_index: int
    prev_log_term: int
    entries: List[LogEntry] = list()
    leader_commit: int


class AppendEntriesResponse(BaseModel):
    term: int
    success: bool


def build_app():
    app = FastAPI()
    state = State()
    state.store = Store()

    # ----- DB Router -----
    @app.get("/")
    async def db_get(key: str) -> ReadResponse:
        """reads the specified value"""
        v = state.store.read(key)
        if not v:
            raise HTTPException(status_code=404, detail="Not found")
        return ReadResponse(value=v)

    @app.post("/", status_code=201)
    async def db_upsert(key: str, value: str):
        """inserts the specified value without checking for previous existence"""
        state.store.upsert(key, value)

    @app.delete("/", status_code=204)
    async def db_delete(key: str):
        """deletes specified key without checking for existence"""
        state.store.delete(key)

    # ----- Raft Router -----
    @app.post("/rpc/append")
    async def rpc_append_entries(req: AppendEntries) -> AppendEntriesResponse:
        """handles AppendEntry RPC requests for writes and heartbeats"""
        res = state.append_entries(
            term=req.term,
            leader_id=req.leader_id,
            prev_log_index=req.prev_log_index,
            prev_log_term=req.prev_log_term,
            entries=req.entries,  # noqa  -- duck-type match
            leader_commit=req.leader_commit)
        return AppendEntriesResponse(term=res.term, success=res.success)

    return app
