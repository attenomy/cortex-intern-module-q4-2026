import cProfile
import gc
import json
import pstats
import statistics
import threading
import time
import tracemalloc
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from modules.semantic_cache.service import SemanticCacheService

RUN_ID = uuid.uuid4().hex
PREFIX = f"bench:ctx003:{RUN_ID}:"
REPORTS = Path("../reports")
REPORTS.mkdir(exist_ok=True)

service = SemanticCacheService()
service.vector_key = PREFIX + "vectors"
service.entry_prefix = PREFIX + "entry:"
service.exact_prefix = PREFIX + "exact:"
service.lock_prefix = PREFIX + "lock:"
service.hits_key = PREFIX + "hits"
service.misses_key = PREFIX + "misses"

results = {
    "run_id": RUN_ID,
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "experiments": {},
    "concurrency": {},
    "memory": {},
    "profiling": {},
}


def percentile(values, p):
    ordered = sorted(values)
    return round(ordered[int((len(ordered) - 1) * p)], 3)


def summarize(values):
    return {
        "requests": len(values),
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": percentile(values, 0.95),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
    }


def timed_lookup(query, threshold=0.95):
    start = time.perf_counter()
    result = service.lookup(query, threshold=threshold)
    elapsed = (time.perf_counter() - start) * 1000

    if not service.is_connected:
        raise RuntimeError("Cache lookup failed; Redis/service disconnected.")

    return result, elapsed


def exact_request():
    result, elapsed = timed_lookup(
        "CTX003 benchmark exact cache request"
    )
    if not result["hit"]:
        raise RuntimeError("Expected exact cache hit, received miss.")
    return elapsed


try:
    print("Checking Redis...")
    if not service.redis_client.ping():
        raise RuntimeError("Redis ping failed.")

    print("Warming up embedding model...")
    service._get_model()
    service._embed("benchmark warmup query")

    print("Creating isolated benchmark entries...")
    service.store(
        "CTX003 benchmark exact cache request",
        {"answer": "benchmark response"},
    )
    service.store(
        "How can I reset my account password?",
        {"answer": "Use the password reset process."},
    )

    # Verify exact lookup.
    exact, exact_ms = timed_lookup(
        "CTX003 benchmark exact cache request"
    )
    if not exact["hit"]:
        raise RuntimeError("Exact lookup verification failed.")

    # Find the semantic similarity score before threshold experiments.
    semantic_query = "What steps should I take to change my account password?"
    semantic, semantic_ms = timed_lookup(semantic_query, threshold=0.0)

    if not semantic["hit"]:
        raise RuntimeError(
            "Semantic baseline did not match. Do not report threshold results."
        )

    semantic_score = semantic["similarity_score"]
    print(f"Semantic baseline score: {semantic_score:.6f}")

    # Six threshold experiments.
    print("\nRunning six threshold experiments...")
    thresholds = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]

    for threshold in thresholds:
        samples = []
        hits = 0

        for _ in range(30):
            result, elapsed = timed_lookup(
                semantic_query,
                threshold=threshold,
            )
            samples.append(elapsed)
            hits += int(result["hit"])

        results["experiments"][str(threshold)] = {
            **summarize(samples),
            "threshold": threshold,
            "hits": hits,
            "hit_rate_percent": round(hits / len(samples) * 100, 2),
            "semantic_similarity_score": semantic_score,
        }

        print(
            f"Threshold {threshold:.2f}: "
            f"hits={hits}/30, median={statistics.median(samples):.3f} ms"
        )

    # High-concurrency exact-hit load tests.
    print("\nRunning concurrency experiments...")

    for workers in [1, 4, 8, 16]:
        per_worker = 100
        barrier = threading.Barrier(workers)

        def worker(barrier=barrier, per_worker=per_worker):
            barrier.wait()
            return [exact_request() for _ in range(per_worker)]

        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            batches = list(executor.map(lambda _: worker(), range(workers)))

        wall_seconds = time.perf_counter() - start
        latencies = [latency for batch in batches for latency in batch]

        results["concurrency"][str(workers)] = {
            **summarize(latencies),
            "workers": workers,
            "total_requests": len(latencies),
            "wall_time_seconds": round(wall_seconds, 3),
            "throughput_requests_per_second": round(
                len(latencies) / wall_seconds, 2
            ),
        }

        print(
            f"{workers} workers: {len(latencies)} requests, "
            f"p95={percentile(latencies, 0.95):.3f} ms"
        )

    # cProfile: 1,000 sequential exact cache requests.
    print("\nRunning cProfile...")
    profiler = cProfile.Profile()
    profiler.enable()

    profile_samples = [exact_request() for _ in range(1000)]

    profiler.disable()

    profile_path = REPORTS / "day14_cprofile.txt"
    with profile_path.open("w", encoding="utf-8") as file:
        stats = pstats.Stats(profiler, stream=file)
        stats.strip_dirs().sort_stats("cumulative").print_stats(30)

    results["profiling"] = {
        "requests": len(profile_samples),
        **summarize(profile_samples),
        "profile_file": str(profile_path),
    }

    # tracemalloc: 5,000 repeated exact cache requests.
    print("\nRunning 5,000-request memory test...")
    gc.collect()
    tracemalloc.start()

    before_current, _ = tracemalloc.get_traced_memory()

    for index in range(5000):
        exact_request()

        if (index + 1) % 1000 == 0:
            print(f"Memory test: {index + 1}/5000")

    gc.collect()
    after_current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    results["memory"] = {
        "requests": 5000,
        "before_current_bytes": before_current,
        "after_current_bytes": after_current,
        "net_growth_bytes": after_current - before_current,
        "peak_traced_bytes": peak,
    }

    # Machine-readable output.
    json_path = REPORTS / "day14_benchmark_results.json"
    json_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    # Human-readable report.
    report_path = REPORTS / "tuning_experiments.md"

    lines = [
        "# CTX-003 Day 14 - Performance and Tuning Experiments",
        "",
        f"- Run ID: `{RUN_ID}`",
        f"- UTC timestamp: `{results['timestamp_utc']}`",
        "- Workload: isolated Redis namespace; exact and semantic cache paths",
        "",
        "## 1. Similarity threshold experiments",
        "",
        "| Threshold | Hits / 30 | Hit rate | Median (ms) | P95 (ms) |",
        "|---:|---:|---:|---:|---:|",
    ]

    for threshold, data in results["experiments"].items():
        lines.append(
            f"| {threshold} | {data['hits']}/30 | "
            f"{data['hit_rate_percent']}% | "
            f"{data['median_ms']} | {data['p95_ms']} |"
        )

    lines += [
        "",
        f"Semantic baseline similarity: `{semantic_score:.6f}`",
        "",
        "## 2. Concurrent exact-hit load tests",
        "",
        "| Workers | Requests | Throughput (req/s) | Median (ms) | P95 (ms) |",
        "|---:|---:|---:|---:|---:|",
    ]

    for workers, data in results["concurrency"].items():
        lines.append(
            f"| {workers} | {data['total_requests']} | "
            f"{data['throughput_requests_per_second']} | "
            f"{data['median_ms']} | {data['p95_ms']} |"
        )

    lines += [
        "",
        "## 3. CPU latency SLA",
        "",
        "Target: median <25 ms and p95 <50 ms.",
        "",
    ]

    for workers, data in results["concurrency"].items():
        passed = data["median_ms"] < 25 and data["p95_ms"] < 50
        lines.append(
            f"- {workers} workers: median `{data['median_ms']} ms`, "
            f"p95 `{data['p95_ms']} ms` - "
            f"{'PASS' if passed else 'FAIL'}"
        )

    lines += [
        "",
        "## 4. cProfile",
        "",
        f"- Requests: {results['profiling']['requests']}",
        f"- Median: {results['profiling']['median_ms']} ms",
        f"- P95: {results['profiling']['p95_ms']} ms",
        f"- Detailed profile: `{profile_path}`",
        "",
        "## 5. tracemalloc - 5,000 requests",
        "",
        f"- Before: {results['memory']['before_current_bytes']} bytes",
        f"- After GC: {results['memory']['after_current_bytes']} bytes",
        f"- Net growth: {results['memory']['net_growth_bytes']} bytes",
        f"- Peak traced memory: {results['memory']['peak_traced_bytes']} bytes",
        "",
        "Interpretation: net Python heap growth is measured after garbage "
        "collection. This is evidence for this workload, not proof of "
        "zero memory leaks.",
        "",
        "## 6. Scope and limitations",
        "",
        "- Thresholds were varied; the production threshold was not changed.",
        "- Concurrency tests used exact cache hits.",
        "- Semantic lookup was measured separately.",
        "- Redis vector quantization and VSIM candidate count were not changed.",
        "- Results apply to this machine, Redis instance, model and workload.",
        "",
    ]

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print("\nBENCHMARK COMPLETE")
    print("JSON:", json_path.resolve())
    print("REPORT:", report_path.resolve())
    print("PROFILE:", profile_path.resolve())

finally:
    # Delete only keys created by this unique benchmark run.
    keys = list(service.redis_client.scan_iter(match=PREFIX + "*"))
    if keys:
        service.redis_client.delete(*keys)

    print("ISOLATED BENCHMARK KEYS CLEANED:", len(keys))
