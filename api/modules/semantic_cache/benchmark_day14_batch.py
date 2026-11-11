import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from modules.semantic_cache.service import SemanticCacheService

BATCH_SIZES = [1, 4, 8, 16, 32]
QUERY_COUNT = 96
TRIALS = 3

REPORTS = Path("../reports")
REPORTS.mkdir(exist_ok=True)

service = SemanticCacheService()

print("Loading CPU embedding model...")
model = service._get_model()

if str(model.device) != "cpu":
    raise RuntimeError("CPU benchmark required.")

queries = [
    f"Semantic cache performance benchmark query number {i}"
    for i in range(QUERY_COUNT)
]

print("Device:", model.device)
print("PyTorch threads:", torch.get_num_threads())
print("Queries:", QUERY_COUNT)

# Warm-up
model.encode(
    queries[:8],
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=False,
)

results = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "device": str(model.device),
    "torch_intra_op_threads": torch.get_num_threads(),
    "query_count": QUERY_COUNT,
    "trials": TRIALS,
    "experiments": {},
}

for batch_size in BATCH_SIZES:
    durations = []

    for _trial in range(TRIALS):
        started = time.perf_counter()

        vectors = model.encode(
            queries,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        elapsed_ms = (time.perf_counter() - started) * 1000

        if vectors.shape != (QUERY_COUNT, service.dimensions):
            raise RuntimeError("Unexpected embedding dimensions.")

        durations.append(elapsed_ms)

    median_ms = statistics.median(durations)

    results["experiments"][str(batch_size)] = {
        "batch_size": batch_size,
        "trial_durations_ms": [round(x, 3) for x in durations],
        "median_total_ms": round(median_ms, 3),
        "median_per_query_ms": round(median_ms / QUERY_COUNT, 3),
        "throughput_queries_per_second": round(
            QUERY_COUNT * 1000 / median_ms, 2
        ),
    }

    print(
        f"Batch {batch_size}: "
        f"median={median_ms:.2f} ms, "
        f"per_query={median_ms / QUERY_COUNT:.3f} ms, "
        f"throughput={QUERY_COUNT * 1000 / median_ms:.2f} queries/sec"
    )

json_path = REPORTS / "day14_batch_size_results.json"
md_path = REPORTS / "day14_batch_size_results.md"

json_path.write_text(json.dumps(results, indent=2))

lines = [
    "# CTX-003 Day 14 - Batch Size Tuning",
    "",
    f"- Device: {results['device']}",
    f"- PyTorch intra-op threads: {results['torch_intra_op_threads']}",
    f"- Queries per trial: {QUERY_COUNT}",
    f"- Trials per batch size: {TRIALS}",
    "",
    "| Batch size | Median total (ms) | Per query (ms) | Throughput (queries/s) |",
    "|---:|---:|---:|---:|",
]

for item in results["experiments"].values():
    lines.append(
        f"| {item['batch_size']} "
        f"| {item['median_total_ms']} "
        f"| {item['median_per_query_ms']} "
        f"| {item['throughput_queries_per_second']} |"
    )

md_path.write_text("\n".join(lines) + "\n")

print("\nBATCH SIZE BENCHMARK COMPLETE")
print("JSON:", json_path.resolve())
print("REPORT:", md_path.resolve())
