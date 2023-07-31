from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from store import Store
from raft import State, Op, Role


# all FastAPI and Pydantic code should be limited to the server module
# (this might have to be flexed for BackgroundTasks depending on performance)
class ReadResponse(BaseModel):
    value: str | None


class LogEntry(BaseModel):
    """This class must match the raft.Entry class"""
    op: Op
    key: str
    value: str | None
    term: int


class AppendEntries(BaseModel):
    term: int
    leader_id: str
    prev_log_index: int
    prev_log_term: int
    entries: List[LogEntry] = list()
    leader_commit: int


class AppendEntriesResponse(BaseModel):
    term: int
    success: bool


def build_app(state: State = None):
    app = FastAPI()
    if not state:
        # dependency injection primarily for test setup and observability
        state = State(Store())

    # Note: Default fastapi behavior for unhandled exceptions is to return a
    # 404. This is incorrect as a 4xx status code indicates a malformed request
    # and should be over-ridden with a general exception middleware that
    # returns a 500. See https://fastapi.tiangolo.com/tutorial/handling-errors/

    # ----- DB Router -----
    @app.get("/")
    async def db_get(key: str) -> ReadResponse:
        """reads the specified value"""
        v = state.store.read(key)
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return ReadResponse(value=v)

    @app.post("/", status_code=status.HTTP_201_CREATED)
    async def db_upsert(key: str, value: str, response: Response):
        """inserts the specified value without checking for previous existence
        """
        if state.role != Role.LEADER:
            return JSONResponse(
                status_code=status.HTTP_308_PERMANENT_REDIRECT,
                content=None,
                headers={'Location': state.voted_for})
        state.store.upsert(key, value)

    @app.delete("/", status_code=status.HTTP_204_NO_CONTENT)
    async def db_delete(key: str):
        """deletes specified key without checking for existence"""
        if state.role != Role.LEADER:
            return JSONResponse(
                status_code=status.HTTP_308_PERMANENT_REDIRECT,
                content=None,
                headers={'Location': state.voted_for})
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
