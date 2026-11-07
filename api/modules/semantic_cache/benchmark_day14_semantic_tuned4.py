import json
import statistics
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import torch
from modules.semantic_cache.service import SemanticCacheService

RUN_ID = uuid.uuid4().hex
PREFIX = f"bench:ctx003:semantic:{RUN_ID}:"
REPORTS = Path("../reports")
REPORTS.mkdir(exist_ok=True)

service = SemanticCacheService()
service.vector_key = PREFIX + "vectors"
service.entry_prefix = PREFIX + "entry:"
service.exact_prefix = PREFIX + "exact:"
service.lock_prefix = PREFIX + "lock:"
service.hits_key = PREFIX + "hits"
service.misses_key = PREFIX + "misses"

STORED_QUERY = "How can I reset my account password?"
SEMANTIC_QUERY = "What steps should I take to change my account password?"
THRESHOLD = 0.70

results = {
    "run_id": RUN_ID,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "model_device": None,
    "threshold": THRESHOLD,
    "concurrency": {},
    "profiling": {},
}


def percentile(values, p):
    ordered = sorted(values)
    return round(ordered[min(int((len(ordered) - 1) * p), len(ordered) - 1)], 3)


def summarize(values):
    return {
        "requests": len(values),
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": percentile(values, 0.95),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
    }


def semantic_request():
    started = time.perf_counter()
    result = service.lookup(SEMANTIC_QUERY, threshold=THRESHOLD)
    elapsed = (time.perf_counter() - started) * 1000

    return {
        "elapsed_ms": elapsed,
        "hit": bool(result.get("hit")),
        "score": result.get("similarity_score", 0.0),
        "timings": result.get("timings", {}),
        "embedding_latency_ms": result.get("embedding_latency_ms", 0.0),
        "redis_latency_ms": result.get("redis_latency_ms", 0.0),
    }


try:
    print("Checking Redis...")
    if not service.redis_client.ping():
        raise RuntimeError("Redis ping failed.")

    torch.set_num_threads(4)
    print("PYTORCH INTRA-OP THREADS:", torch.get_num_threads())
    print("Loading CPU embedding model...")
    model = service._get_model()
    results["model_device"] = str(model.device)
    print("MODEL DEVICE:", model.device)

    if str(model.device) != "cpu":
        raise RuntimeError("This benchmark requires CPU inference.")

    service._embed("Warmup semantic benchmark")

    print("Creating isolated semantic cache entry...")
    service.store(
        STORED_QUERY,
        {"answer": "Use the password reset process."},
    )

    baseline = semantic_request()
    print("Baseline:", baseline)

    if not baseline["hit"]:
        raise RuntimeError(
            "Semantic baseline failed. No concurrency tests were run."
        )

    results["baseline"] = baseline

    print("\nRunning concurrent semantic lookups...")

    for workers in [1, 4, 8, 16]:
        per_worker = 20
        barrier = threading.Barrier(workers)

        def worker(worker_id, barrier=barrier, per_worker=per_worker):
            samples = []

            barrier.wait()
            for _ in range(per_worker):
                samples.append(semantic_request())

            return samples

        started = time.perf_counter()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            batches = list(
                executor.map(worker, range(workers))
            )

        wall_seconds = time.perf_counter() - started
        requests = [item for batch in batches for item in batch]
        latencies = [item["elapsed_ms"] for item in requests]
        hits = sum(item["hit"] for item in requests)
        misses = len(requests) - hits

        data = {
            **summarize(latencies),
            "workers": workers,
            "total_requests": len(requests),
            "hits": hits,
            "misses": misses,
            "hit_rate_percent": round(hits / len(requests) * 100, 2),
            "wall_time_seconds": round(wall_seconds, 3),
            "throughput_requests_per_second": round(
                len(requests) / wall_seconds, 2
            ),
            "embedding_median_ms": round(
                statistics.median(
                    item["embedding_latency_ms"] for item in requests
                ), 3
            ),
            "redis_median_ms": round(
                statistics.median(
                    item["redis_latency_ms"] for item in requests
                ), 3
            ),
        }

        results["concurrency"][str(workers)] = data

        print(
            f"{workers} workers: requests={len(requests)}, "
            f"hits={hits}, misses={misses}, "
            f"median={data['median_ms']} ms, "
            f"p95={data['p95_ms']} ms"
        )

    json_path = REPORTS / "day14_semantic_concurrency.json"
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    report_path = REPORTS / "day14_semantic_concurrency.md"
    lines = [
        "# CTX-003 Day 14 — CPU Semantic Concurrency",
        "",
        f"- Run ID: `{RUN_ID}`",
        f"- Timestamp UTC: `{results['timestamp_utc']}`",
        f"- Model device: `{results['model_device']}`",
        f"- Similarity threshold: `{THRESHOLD}`",
        f"- Baseline similarity score: `{baseline['score']}`",
        "",
        "| Workers | Requests | Hits | Misses | Median (ms) | P95 (ms) | Throughput (req/s) | SLA |",
        "|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]

    for workers, data in results["concurrency"].items():
        passed = data["median_ms"] < 25 and data["p95_ms"] < 50
        lines.append(
            f"| {workers} | {data['total_requests']} | "
            f"{data['hits']} | {data['misses']} | "
            f"{data['median_ms']} | {data['p95_ms']} | "
            f"{data['throughput_requests_per_second']} | "
            f"{'PASS' if passed else 'FAIL'} |"
        )

    lines += [
        "",
        "## Profiling",
        "",
        "Concurrent latency was measured using the async worker harness.",
        "Sequential cProfile results are available in day14_cprofile.txt from the original benchmark.",
        "",
        "## Limitations",
        "",
        "- This measures semantic lookups with CPU embedding and Redis VSIM.",
        "- The workload uses one stored query and one semantically related query.",
        "- Twenty requests were run per worker.",
        "- A miss is counted separately; it is not silently treated as a hit.",
        "- Results apply to this machine and this workload.",
    ]

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\nSEMANTIC CONCURRENCY BENCHMARK COMPLETE")
    print("JSON:", json_path.resolve())
    print("REPORT:", report_path.resolve())

finally:
    keys = list(service.redis_client.scan_iter(match=PREFIX + "*"))
    if keys:
        service.redis_client.delete(*keys)

    print("ISOLATED SEMANTIC BENCHMARK KEYS CLEANED:", len(keys))
