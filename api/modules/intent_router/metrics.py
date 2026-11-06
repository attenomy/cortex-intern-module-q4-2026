"""In-process Prometheus metrics for the intent router (no extra dependency).

Exposed at GET /api/v1/router/metrics in the Prometheus text exposition format. Counters live in
process memory, are thread safe, and reset when the process restarts (normal for Prometheus counters).
Requests rejected by request validation (HTTP 422) never reach our code, so they are not counted here.
"""
import threading

LATENCY_BUCKETS_MS = (1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 1000.0)
OUTCOMES = ("routed", "fallback", "bad_request", "not_ready", "error")
INTENTS = ("finance", "support", "search", "orchestration")


class RouterMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self._outcomes = dict.fromkeys(OUTCOMES, 0)
        self._intents = dict.fromkeys(INTENTS, 0)
        self._buckets = [0] * len(LATENCY_BUCKETS_MS)
        self._sum_ms = 0.0
        self._count = 0

    def record(self, outcome, intent=None, latency_ms=None):
        with self._lock:
            self._outcomes[outcome] += 1
            if intent is not None:
                self._intents[intent] += 1
            if latency_ms is not None:
                self._sum_ms += latency_ms
                self._count += 1
                for i, upper in enumerate(LATENCY_BUCKETS_MS):
                    if latency_ms <= upper:
                        self._buckets[i] += 1
                        break

    def render(self, model_ready):
        with self._lock:
            outcomes, intents = dict(self._outcomes), dict(self._intents)
            buckets, total_ms, count = list(self._buckets), self._sum_ms, self._count
        out = ["# HELP cortex_intent_router_model_ready 1 when the ONNX model is loaded and warmed up",
               "# TYPE cortex_intent_router_model_ready gauge",
               f"cortex_intent_router_model_ready {1 if model_ready else 0}",
               "# HELP cortex_intent_router_requests_total Requests handled by the router, by outcome",
               "# TYPE cortex_intent_router_requests_total counter"]
        out += [f'cortex_intent_router_requests_total{{outcome="{o}"}} {outcomes[o]}' for o in OUTCOMES]
        out += ["# HELP cortex_intent_router_intent_total Routing decisions by final intent (fallbacks count as search)",
                "# TYPE cortex_intent_router_intent_total counter"]
        out += [f'cortex_intent_router_intent_total{{intent="{i}"}} {intents[i]}' for i in INTENTS]
        out += ["# HELP cortex_intent_router_latency_ms Router execution time in milliseconds (latency_ms field)",
                "# TYPE cortex_intent_router_latency_ms histogram"]
        running = 0
        for upper, n in zip(LATENCY_BUCKETS_MS, buckets):
            running += n
            out.append(f'cortex_intent_router_latency_ms_bucket{{le="{upper}"}} {running}')
        out += [f'cortex_intent_router_latency_ms_bucket{{le="+Inf"}} {count}',
                f"cortex_intent_router_latency_ms_sum {total_ms:.3f}",
                f"cortex_intent_router_latency_ms_count {count}"]
        return "\n".join(out) + "\n"
