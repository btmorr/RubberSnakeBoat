from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Union
from store import Store
from raft import State, AppendEntries, AppendEntriesResponse


class ReadResponse(BaseModel):
    value: Union[str, None]


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
        return state.append_entries_receiver(req)

    return app
