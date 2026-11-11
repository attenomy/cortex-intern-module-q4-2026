"""Trivial app with the SAME web stack as Cortex (uvicorn + FastAPI + pydantic + sync endpoint in the
threadpool) but NO model. Used by `load_test.py --baseline` to measure how much latency under load
comes from the web stack and the load generator rather than from the intent router."""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Q(BaseModel):
    query: str


@app.post("/echo")
def echo(q: Q):
    return {"ok": True, "chars": len(q.query)}
