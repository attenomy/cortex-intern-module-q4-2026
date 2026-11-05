"""Day 14, part 2: concurrent load tests for the intent router.

Modes
  (default)      real `uvicorn main:app` server, HTTP clients at 1 / 10 / 50 concurrency (closed loop)
  --rates R ...  OPEN-LOOP test: requests arrive at a fixed rate (req/s) for --duration seconds no matter
                 how fast the server answers; latency is measured from each request's intended send time.
                 This is the realistic way to state "p95 under load". (In a closed-loop test with N clients,
                 Little's law gives latency ~ N / throughput: 50 clients at 50 ms needs 1000 req/s.)
  --baseline     same web stack with NO model (baseline_app.py): the ceiling of uvicorn + FastAPI + this load
                 generator on this machine
  --inprocess    no HTTP: N threads call SemanticRouter.route_query directly (the model-serving core)
Options
  --threads K    INTENT_ROUTER_THREADS (ONNX intra-op threads)
  --env K=V ...  any other environment variable for the server / router, e.g.
                 --env INTENT_ROUTER_MAX_CONCURRENCY=2 --env INTENT_ROUTER_SPIN=0

Every level is preceded by a short warm-up that is not reported. Reported per level: p50/p90/p95/p99 of
  client latency = what the caller sees (includes queueing when the system is saturated)
  server latency = `latency_ms` returned by the router (tokenize + inference + softmax)
plus throughput, non-200 responses and (HTTP modes) peak memory of the whole server process tree.
The load generator runs on the same machine, so it competes with the server for CPU.

Run from the repo root, e.g.:  python api/modules/intent_router/profiling/load_test.py --inprocess
Output: reports/load_test_results[_mode][_openloop][_tags].md and .json
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import httpx
import psutil

from common import API_DIR, REPORTS, hardware, percentiles, query_pool

PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))


def start_server(app_target, cwd, env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app_target, "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning"],
        cwd=cwd, env=env)


def wait_ready(url, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if httpx.post(url, json={"query": "warm up"}, timeout=5).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def tree_rss(proc):
    """RSS of a process and all its children (on Windows a venv's python.exe is a launcher that starts the
    real interpreter as a child, so the parent alone shows only a few MB)."""
    total = 0
    for p in [proc] + proc.children(recursive=True):
        try:
            total += p.memory_info().rss
        except psutil.Error:
            pass
    return total


class RssSampler(threading.Thread):
    def __init__(self, pid):
        super().__init__(daemon=True)
        self.proc, self.peak, self.stop = psutil.Process(pid), 0, False

    def run(self):
        while not self.stop:
            self.peak = max(self.peak, tree_rss(self.proc))
            time.sleep(0.2)


def summarize(concurrency, total, wall, client_ms, server_ms, codes):
    return {"concurrency": concurrency, "requests": total, "status_codes": {str(k): v for k, v in codes.items()},
            "throughput_rps": total / wall,
            "client": percentiles(client_ms) if client_ms else None,
            "server": percentiles(server_ms) if server_ms else None}


async def post(session, url, query, codes, client_ms, server_ms, started):
    try:
        async with session.post(url, json={"query": query}) as r:
            body = await r.json(content_type=None) if r.status == 200 else None
            dt = (time.perf_counter() - started) * 1000
            codes[r.status] = codes.get(r.status, 0) + 1
    except Exception:
        codes["error"] = codes.get("error", 0) + 1
        return
    if body is not None:
        client_ms.append(dt)
        if "latency_ms" in body:
            server_ms.append(body["latency_ms"])


async def run_level_http(url, concurrency, total, pool):
    client_ms, server_ms, codes = [], [], {}
    sem = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=concurrency),
                                     timeout=aiohttp.ClientTimeout(total=120)) as session:
        async def one(i):
            async with sem:
                await post(session, url, pool[i % len(pool)], codes, client_ms, server_ms, time.perf_counter())
        t0 = time.perf_counter()
        await asyncio.gather(*(one(i) for i in range(total)))
        wall = time.perf_counter() - t0
    return summarize(concurrency, total, wall, client_ms, server_ms, codes)


async def run_rate_http(url, rate, duration, pool):
    client_ms, server_ms, codes = [], [], {}
    total = int(rate * duration)
    state = {"inflight": 0, "peak": 0}
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0),
                                     timeout=aiohttp.ClientTimeout(total=120)) as session:
        async def one(i, due):
            state["inflight"] += 1
            state["peak"] = max(state["peak"], state["inflight"])
            try:
                await post(session, url, pool[i % len(pool)], codes, client_ms, server_ms, due)   # from intended send time
            finally:
                state["inflight"] -= 1
        t0 = time.perf_counter()
        tasks = []
        for i in range(total):
            due = t0 + i / rate
            delay = due - time.perf_counter()
            if delay > 0:
                await asyncio.sleep(delay)
            tasks.append(asyncio.create_task(one(i, due)))
        await asyncio.gather(*tasks)
        wall = time.perf_counter() - t0
    out = summarize(state["peak"], total, wall, client_ms, server_ms, codes)
    out["target_rps"] = rate
    return out


def run_level_inprocess(router, concurrency, total, pool):
    def one(i):
        t = time.perf_counter()
        r = router.route_query(pool[i % len(pool)])
        return (time.perf_counter() - t) * 1000, r["latency_ms"]

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        res = list(ex.map(one, range(total)))
    wall = time.perf_counter() - t0
    return summarize(concurrency, total, wall, [a for a, _ in res], [b for _, b in res], {"200": total})


def fmt(p, k):
    return "-" if p is None else f"{p[k]:.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=None, help="INTENT_ROUTER_THREADS")
    ap.add_argument("--env", action="append", default=[], metavar="K=V", help="extra environment variable (repeatable)")
    ap.add_argument("--levels", type=int, nargs="+", default=[1, 10, 50])
    ap.add_argument("--requests", type=int, default=2000, help="requests per concurrency level")
    ap.add_argument("--rates", type=int, nargs="+", default=None, help="open-loop test at these req/s (HTTP modes)")
    ap.add_argument("--duration", type=int, default=10, help="seconds per rate for --rates")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--baseline", action="store_true", help="web stack without the model")
    mode.add_argument("--inprocess", action="store_true", help="threads call route_query directly (no HTTP)")
    args = ap.parse_args()

    env_extra = dict(kv.split("=", 1) for kv in args.env)
    if args.threads:
        env_extra["INTENT_ROUTER_THREADS"] = str(args.threads)
    name = "baseline" if args.baseline else ("inprocess" if args.inprocess else "http")
    open_loop = bool(args.rates) and not args.inprocess

    pool = query_pool()
    peak_mb = None
    if args.inprocess:
        os.environ.update(env_extra)
        from modules.intent_router.service import SemanticRouter
        router = SemanticRouter()
        router.load()
        results = []
        for c in args.levels:
            run_level_inprocess(router, c, 300, pool)                  # warm-up, not reported
            results.append(run_level_inprocess(router, c, args.requests, pool))
    else:
        target, cwd, path = ("baseline_app:app", HERE, "/echo") if args.baseline else ("main:app", str(API_DIR), "/api/v1/router")
        url = f"http://127.0.0.1:{PORT}{path}"
        server = start_server(target, cwd, env_extra)
        try:
            if not wait_ready(url):
                sys.exit("server did not become ready (is the model in api/modules/intent_router/models/ ?)")
            sampler = RssSampler(server.pid)
            sampler.start()
            results = []
            if open_loop:
                for r in args.rates:
                    asyncio.run(run_rate_http(url, min(r, 50), 3, pool))              # warm-up, not reported
                    results.append(asyncio.run(run_rate_http(url, r, args.duration, pool)))
            else:
                for c in args.levels:
                    asyncio.run(run_level_http(url, c, 300, pool))                    # warm-up, not reported
                    results.append(asyncio.run(run_level_http(url, c, args.requests, pool)))
            sampler.stop = True
            peak_mb = sampler.peak / 1e6
        finally:
            server.terminate()
            server.wait(timeout=20)

    if open_loop:
        hdr = ("| target req/s | achieved req/s | peak in flight | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |\n"
               "|---|---|---|---|---|---|---|---|---|---|\n")
    else:
        hdr = ("| concurrency | req/s | client p50 | p90 | p95 | p99 | server p50 | p95 | non-200 |\n"
               "|---|---|---|---|---|---|---|---|---|\n")
    body = ""
    for r in results:
        bad = sum(v for k, v in r["status_codes"].items() if k != "200")
        lead = f"{r['target_rps']} | {r['throughput_rps']:.0f} | {r['concurrency']}" if open_loop else f"{r['concurrency']} | {r['throughput_rps']:.0f}"
        body += (f"| {lead} | {fmt(r['client'], 'p50')} | {fmt(r['client'], 'p90')} | {fmt(r['client'], 'p95')} | "
                 f"{fmt(r['client'], 'p99')} | {fmt(r['server'], 'p50')} | {fmt(r['server'], 'p95')} | {bad} |\n")
    settings = ", ".join(f"{k}={v}" for k, v in env_extra.items()) or "defaults"
    md = (f"# Load test results ({name}{', open-loop' if open_loop else ''})\n\nHardware: `{json.dumps(hardware())}`\n\n"
          f"settings: {settings} | " + (f"{args.duration} s per rate | " if open_loop else f"{args.requests} requests per level | ")
          + "~5% of requests are 10,000-character payloads | all times in ms\n\n" + hdr + body)
    if peak_mb is not None:
        md += f"\nServer peak RSS (process tree): {peak_mb:.0f} MB\n"
    tags = "".join("_" + k.replace("INTENT_ROUTER_", "").lower() + v for k, v in env_extra.items())
    suffix = ("" if name == "http" else f"_{name}") + ("_openloop" if open_loop else "") + tags
    (REPORTS / f"load_test_results{suffix}.md").write_text(md, encoding="utf-8")
    (REPORTS / f"load_test_results{suffix}.json").write_text(
        json.dumps({"mode": name, "settings": env_extra, "hardware": hardware(), "server_peak_rss_mb": peak_mb, "levels": results}, indent=2),
        encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
