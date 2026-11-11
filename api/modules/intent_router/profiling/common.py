"""Shared helpers for the Day 14 profiling scripts."""
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np

MODULE_DIR = Path(__file__).resolve().parents[1]          # .../api/modules/intent_router
API_DIR = MODULE_DIR.parents[1]                            # .../api
sys.path.insert(0, str(API_DIR))                           # so `modules.intent_router...` imports work
MODEL_DIR = Path(os.getenv("INTENT_ROUTER_MODEL_DIR") or MODULE_DIR / "models")
DATASET = MODULE_DIR / "data" / "intent_dataset.json"
REPORTS = MODULE_DIR / "reports"
FIGURES = REPORTS / "figures"
REPORTS.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


def load_samples(split, ambiguous=None):
    doc = json.loads(DATASET.read_text(encoding="utf-8"))
    return [s for s in doc["samples"] if s["split"] == split
            and (ambiguous is None or s["ambiguous"] == ambiguous)]


def long_payload():
    """Worst-case request: exactly 10,000 characters (the API limit)."""
    return ("invoice total login workflow " * 400)[:10_000]


def query_pool(n_long_every=20):
    """Realistic mix: dataset queries with a 10,000-character payload every `n_long_every` items."""
    texts = [s["text"] for s in load_samples("validation") + load_samples("train")[:40]]
    pool = []
    for i, t in enumerate(texts):
        pool.append(t)
        if i % n_long_every == n_long_every - 1:
            pool.append(long_payload())
    return pool


def percentiles(values_ms):
    a = np.asarray(values_ms, dtype=np.float64)
    return {"n": int(a.size), "p50": float(np.percentile(a, 50)), "p90": float(np.percentile(a, 90)),
            "p95": float(np.percentile(a, 95)), "p99": float(np.percentile(a, 99)), "max": float(a.max())}


def hardware():
    info = {"python": platform.python_version(), "os": platform.platform(),
            "cpu": platform.processor() or "unknown", "logical_cpus": os.cpu_count()}
    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
    except ImportError:
        pass
    try:
        import onnxruntime
        info["onnxruntime"] = onnxruntime.__version__
    except ImportError:
        pass
    return info
