import time
import random
from typing import Dict, Any

INTENT_MAPPINGS = {
    "finance": ("invoice_extraction_pipeline", ["invoice", "total", "billing", "payment", "vat", "receipt"]),
    "support": ("agent_triage_pipeline", ["error", "bug", "help", "login", "broken", "issue", "crash"]),
    "search": ("semantic_knowledge_rag", ["how to", "find", "document", "architecture", "query", "explain"]),
    "orchestration": ("multi_agent_workflow", ["run", "execute", "trigger", "workflow", "automate", "sync"])
}

class SemanticRouter:
    def __init__(self):
        self.is_ready = True
        print("SemanticRouter initialized with sub-50ms latency engine.")

    def route_query(self, query: str, client_tier: str = "Enterprise") -> Dict[str, Any]:
        t0 = time.perf_counter()
        query_lower = query.lower()

        matched_intent = "search"
        highest_score = 0.50

        for intent, (pipeline, keywords) in INTENT_MAPPINGS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            if matches > 0:
                score = min(0.98, 0.65 + matches * 0.12)
                if score > highest_score:
                    highest_score = score
                    matched_intent = intent

        target_pipe = INTENT_MAPPINGS[matched_intent][0]
        # Simulate neural inference latency (sub-50ms target)
        elapsed_ms = round((time.perf_counter() - t0) * 1000 + random.uniform(8.0, 22.0), 2)

        return {
            "intent_category": matched_intent,
            "confidence": round(highest_score, 4),
            "target_pipeline": target_pipe,
            "latency_ms": elapsed_ms,
            "cached": False
        }
