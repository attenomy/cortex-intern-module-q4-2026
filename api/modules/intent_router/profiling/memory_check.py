"""Day 14, part 4: memory-leak check over 5,000 continuous requests (tracemalloc + RSS).

After loading and warming up, sends 5,000 route_query calls in 5 blocks of 1,000 (a 10,000-character
payload every 20th request). After each block it forces a garbage collection and records
  * tracemalloc current memory (Python allocations, tracks leaks in our code), and
  * process RSS (everything, including onnxruntime's native memory).
Verdict: growth from block 1 to block 5 must stay below the thresholds below.

Run from the repo root:
    python api/modules/intent_router/profiling/memory_check.py
Output: reports/memory_check.md and reports/memory_check.json
"""
import gc
import json
import tracemalloc

import psutil

from common import REPORTS, hardware, query_pool
from modules.intent_router.service import SemanticRouter

BLOCKS, PER_BLOCK = 5, 1000
MAX_PY_GROWTH_KB = 512        # tracemalloc growth block 1 -> block 5
MAX_RSS_GROWTH_MB = 10        # RSS growth block 1 -> block 5 (allocator noise tolerated)
RSS_LIMIT_MB = 250            # ticket: model memory residency


def main():
    proc = psutil.Process()
    router = SemanticRouter()
    router.load()
    pool = query_pool()
    rss_after_load = proc.memory_info().rss / 1e6

    tracemalloc.start(10)
    snaps, rows, i = [], [], 0
    for b in range(1, BLOCKS + 1):
        for _ in range(PER_BLOCK):
            router.route_query(pool[i % len(pool)])
            i += 1
        gc.collect()
        py_kb = tracemalloc.get_traced_memory()[0] / 1024
        rss_mb = proc.memory_info().rss / 1e6
        rows.append({"block": b, "requests": i, "python_kb": py_kb, "rss_mb": rss_mb})
        snaps.append(tracemalloc.take_snapshot())
        print(f"after {i:5d} requests: python (tracemalloc) {py_kb:8.1f} KB | RSS {rss_mb:7.1f} MB")

    py_growth = rows[-1]["python_kb"] - rows[0]["python_kb"]
    rss_growth = rows[-1]["rss_mb"] - rows[0]["rss_mb"]
    top = snaps[-1].compare_to(snaps[0], "lineno")[:5]
    ok = py_growth < MAX_PY_GROWTH_KB and rss_growth < MAX_RSS_GROWTH_MB
    verdict = "PASS" if ok else "FAIL"
    lines = [f"# Memory check ({BLOCKS * PER_BLOCK} requests)\n", f"Hardware: `{json.dumps(hardware())}`\n",
             "| after requests | Python KB (tracemalloc) | RSS MB |\n|---|---|---|\n"]
    lines += [f"| {r['requests']} | {r['python_kb']:.1f} | {r['rss_mb']:.1f} |\n" for r in rows]
    lines += [f"\nGrowth block 1 -> block {BLOCKS}: Python {py_growth:+.1f} KB (limit {MAX_PY_GROWTH_KB}), "
              f"RSS {rss_growth:+.1f} MB (limit {MAX_RSS_GROWTH_MB})\n",
              f"RSS right after model load: {rss_after_load:.0f} MB; after the run: {rows[-1]['rss_mb']:.0f} MB "
              f"(ticket limit {RSS_LIMIT_MB} MB for this process; the full API process is measured in load_test)\n",
              f"\n**Verdict: {verdict}**\n\nTop allocation differences (block 5 vs block 1):\n\n```\n"
              + "\n".join(str(s) for s in top) + "\n```\n"]
    (REPORTS / "memory_check.md").write_text("".join(lines), encoding="utf-8")
    (REPORTS / "memory_check.json").write_text(json.dumps({"rows": rows, "python_growth_kb": py_growth,
                                                           "rss_growth_mb": rss_growth, "verdict": verdict,
                                                           "rss_after_load_mb": rss_after_load}, indent=2), encoding="utf-8")
    print(f"\nPython growth {py_growth:+.1f} KB | RSS growth {rss_growth:+.1f} MB | RSS after load {rss_after_load:.0f} MB")
    print("VERDICT:", verdict)


if __name__ == "__main__":
    main()
