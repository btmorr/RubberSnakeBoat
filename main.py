from fastapi import FastAPI, HTTPException
from store import Store

app = FastAPI()
app.store = Store()


@app.get("/")
async def db_get(key: str):
    """reads the specified value"""
    v = app.store.read(key)
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    return v


@app.post("/", status_code=201)
async def db_upsert(key: str, value: str):
    """inserts the specified value without checking for previous existence"""
    app.store.upsert(key, value)


@app.delete("/", status_code=204)
async def db_delete(key: str):
    """deletes specified key without checking for existence"""
    app.store.delete(key)

