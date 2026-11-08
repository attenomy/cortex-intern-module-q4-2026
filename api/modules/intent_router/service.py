"""Neural semantic intent router for Attenomy Cortex (CTX-001).

Serving path = onnxruntime + tokenizers + numpy only (no torch / transformers), so the
process stays well inside the 250 MB memory budget.

Thread safety: a request only reads shared objects. ``InferenceSession.run`` and
``Tokenizer.encode`` can be called from several threads at once; the tokenizer's
truncation is configured once in ``load()`` and never changed afterwards. Nothing
per-request is stored on ``self``.
"""
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

import numpy as np

from .schemas import FALLBACK_THRESHOLD, IntentCategory

logger = logging.getLogger(__name__)

PIPELINES = {
    IntentCategory.FINANCE: "invoice_extraction_pipeline",
    IntentCategory.SUPPORT: "agent_triage_pipeline",
    IntentCategory.SEARCH: "semantic_knowledge_rag",
    IntentCategory.ORCHESTRATION: "multi_agent_workflow",
}
FALLBACK_INTENT = IntentCategory.SEARCH
DEFAULT_MODEL_DIR = Path(__file__).resolve().parent / "models"
WARMUP_QUERIES = ("warm up query", "extract the invoice total", "my login is broken")


class ModelNotReadyError(RuntimeError):
    """route_query() was called before load() finished (or load() failed)."""


def softmax(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """P(k) = exp(z_k / T) / sum_j exp(z_j / T), computed with max-subtraction for stability."""
    z = np.asarray(logits, dtype=np.float64) / temperature
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()


class SemanticRouter:
    """Semantic query routing engine (fine-tuned MiniLM exported to ONNX)."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir or os.getenv("INTENT_ROUTER_MODEL_DIR") or DEFAULT_MODEL_DIR)
        self.is_ready = False
        self.labels: list[IntentCategory] = []
        self.temperature = 1.0
        self.max_len = 64
        self._session = None
        self._tokenizer = None
        self._load_attempted = False
        self._load_lock = threading.Lock()
        self._gate = None          # optional cap on concurrent inferences (INTENT_ROUTER_MAX_CONCURRENCY)

    # ------------------------------------------------------------------ startup
    def ensure_loaded(self) -> None:
        """Safety net for callers that never ran the app lifespan (e.g. a plain
        ``TestClient(app)``): load once on first use. Production loads at startup, so this
        is a no-op there. A failed load is not retried on every request."""
        if self.is_ready or self._load_attempted:
            return
        with self._load_lock:
            if self.is_ready or self._load_attempted:
                return
            try:
                self.load()
            except Exception:
                logger.exception("lazy model load failed; requests will get 503")

    def load(self) -> None:
        """Load model + tokenizer once, then warm up. Called from the router lifespan."""
        # Imported here so that importing this module never fails (and never breaks the
        # shared API app) on a machine that has not installed the new requirements yet.
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self._load_attempted = True
        self.is_ready = False
        t0 = time.perf_counter()
        d = self.model_dir

        id2label = json.loads((d / "labels.json").read_text(encoding="utf-8"))
        self.labels = [IntentCategory(id2label[str(i)]) for i in range(len(id2label))]
        cal = json.loads((d / "calibration.json").read_text(encoding="utf-8"))
        self.max_len = int(cal["max_len"])
        self.temperature = float(os.getenv("INTENT_ROUTER_TEMPERATURE", cal["temperature"]))
        if self.temperature <= 0:
            raise ValueError("temperature must be > 0")

        tokenizer = Tokenizer.from_file(str(d / "tokenizer.json"))
        tokenizer.enable_truncation(max_length=self.max_len)

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = int(os.getenv("INTENT_ROUTER_THREADS", min(4, os.cpu_count() or 1)))
        opts.inter_op_num_threads = 1
        if os.getenv("INTENT_ROUTER_SPIN", "1") == "0":
            # ORT's worker threads busy-wait by default; turning that off can help when many requests overlap
            opts.add_session_config_entry("session.intra_op.allow_spinning", "0")
        max_conc = int(os.getenv("INTENT_ROUTER_MAX_CONCURRENCY", "0"))   # 0 = unlimited (default)
        self._gate = threading.BoundedSemaphore(max_conc) if max_conc > 0 else None
        session = ort.InferenceSession(
            str(d / os.getenv("INTENT_ROUTER_MODEL_FILE", "model.onnx")), sess_options=opts, providers=["CPUExecutionProvider"]
        )
        if {i.name for i in session.get_inputs()} != {"input_ids", "attention_mask"}:
            raise ValueError("unexpected ONNX inputs; re-export the model")

        self._tokenizer, self._session = tokenizer, session
        for q in WARMUP_QUERIES:          # no cold-start latency for the first real request
            self._logits(q)
        self.is_ready = True
        logger.info(
            "intent router ready: labels=%s T=%.3f max_len=%d threads=%d load=%.0fms",
            [c.value for c in self.labels], self.temperature, self.max_len,
            opts.intra_op_num_threads, (time.perf_counter() - t0) * 1000,
        )

    # ---------------------------------------------------------------- inference
    def _logits(self, query: str) -> np.ndarray:
        enc = self._tokenizer.encode(query)          # truncated to max_len tokens
        ids = np.asarray([enc.ids], dtype=np.int64)
        mask = np.asarray([enc.attention_mask], dtype=np.int64)
        feeds = {"input_ids": ids, "attention_mask": mask}
        if self._gate is None:
            out = self._session.run(["logits"], feeds)[0]
        else:                                           # extra requests wait here instead of oversubscribing the CPU
            with self._gate:
                out = self._session.run(["logits"], feeds)[0]
        return np.asarray(out[0], dtype=np.float64)

    def route_query(self, query: str, client_tier: str = "Enterprise", max_candidates: int = 3) -> dict[str, Any]:
        if not self.is_ready:
            raise ModelNotReadyError("intent router model is not loaded")
        t0 = time.perf_counter()

        logits = self._logits(query)
        k_total = len(self.labels)
        if np.all(np.isfinite(logits)):
            probs = softmax(logits, self.temperature)
        else:                                          # NaN / inf: fail safe to fallback
            logger.error("non-finite logits for a query of %d chars; forcing fallback", len(query))
            probs = np.full(k_total, 1.0 / k_total)

        order = np.argsort(-probs, kind="stable")[: max(1, min(max_candidates, k_total))]
        top_k = [
            {"intent_category": self.labels[i].value, "confidence": round(float(probs[i]), 4)}
            for i in order
        ]
        confidence = top_k[0]["confidence"]
        # The decision uses the same 4-decimal confidence that is returned to the caller,
        # so the response can never contradict itself (fallback <=> confidence < 0.60).
        fallback = confidence < FALLBACK_THRESHOLD
        intent = FALLBACK_INTENT if fallback else self.labels[order[0]]

        return {
            "intent_category": intent.value,
            "confidence": confidence,
            "fallback_triggered": fallback,
            "target_pipeline": PIPELINES[intent],
            "top_k": top_k,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 3),
            "cached": False,
        }
