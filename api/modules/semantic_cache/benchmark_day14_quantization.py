import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from modules.semantic_cache.service import SemanticCacheService

service = SemanticCacheService()
model = service._get_model()

if str(model.device) != "cpu":
    raise RuntimeError("CPU benchmark required.")

queries = [
    "How can I reset my account password?",
    "What steps should I take to change my account password?",
    "Explain Python programming.",
    "What is the Python programming language?",
    "How do I improve application performance?",
    "Describe semantic caching and vector search.",
    "How can I troubleshoot a database connection?",
    "What are the benefits of machine learning?",
]

vectors = model.encode(
    queries,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=False,
)

vectors = np.asarray(vectors, dtype=np.float32)

# Symmetric int8 quantization using one scale for the vector matrix.
scale = float(np.max(np.abs(vectors)) / 127.0)

if scale == 0:
    raise RuntimeError("Invalid zero quantization scale.")

quantized = np.clip(
    np.rint(vectors / scale),
    -127,
    127
).astype(np.int8)

restored = quantized.astype(np.float32) * scale

original_norms = np.linalg.norm(vectors, axis=1)
restored_norms = np.linalg.norm(restored, axis=1)

original_cosine = vectors @ vectors.T
restored_cosine = (
    restored @ restored.T
    / np.outer(restored_norms, restored_norms)
)

difference = np.abs(original_cosine - restored_cosine)

float_bytes = vectors.nbytes
int8_bytes = quantized.nbytes

results = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "device": str(model.device),
    "dimensions": int(vectors.shape[1]),
    "vector_count": int(vectors.shape[0]),
    "quantization": "symmetric int8 simulation",
    "scale": scale,
    "float32_bytes": int(float_bytes),
    "int8_bytes": int(int8_bytes),
    "storage_reduction_percent": round(
        (1 - int8_bytes / float_bytes) * 100, 3
    ),
    "cosine_similarity_max_absolute_drift": round(
        float(np.max(difference)), 8
    ),
    "cosine_similarity_mean_absolute_drift": round(
        float(np.mean(difference)), 8
    ),
    "cosine_similarity_p95_absolute_drift": round(
        float(np.percentile(difference, 95)), 8
    ),
    "minimum_restored_vector_norm": round(
        float(np.min(restored_norms)), 8
    ),
}

report_dir = Path("../reports")
report_dir.mkdir(exist_ok=True)

json_path = report_dir / "day14_quantization_results.json"
md_path = report_dir / "day14_quantization_results.md"

json_path.write_text(json.dumps(results, indent=2))

md = f"""# CTX-003 Day 14 - Quantization Experiment

- Device: {results['device']}
- Representation: {results['quantization']}
- Vector count: {results['vector_count']}
- Dimensions: {results['dimensions']}

| Metric | Result |
|---|---:|
| Float32 storage | {float_bytes} bytes |
| Int8 storage | {int8_bytes} bytes |
| Storage reduction | {results['storage_reduction_percent']}% |
| Maximum cosine drift | {results['cosine_similarity_max_absolute_drift']} |
| Mean cosine drift | {results['cosine_similarity_mean_absolute_drift']} |
| P95 cosine drift | {results['cosine_similarity_p95_absolute_drift']} |
| Minimum restored vector norm | {results['minimum_restored_vector_norm']} |

**Limitation:** This is an in-memory symmetric int8 quantization simulation.
It does not reconfigure or benchmark Redis VSET's native int8 quantization.
"""

md_path.write_text(md)

print(json.dumps(results, indent=2))
print("\nQUANTIZATION BENCHMARK COMPLETE")
print("JSON:", json_path.resolve())
print("REPORT:", md_path.resolve())
