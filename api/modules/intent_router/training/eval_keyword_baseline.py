"""The ORIGINAL keyword router (INTENT_MAPPINGS, before CTX-001) evaluated on the test split.

This is the "before" number for the error analysis. It is a rejected alternative, not a model that is
being tuned, so running it on the test split does not break the one-time rule.

Run from the repo root:
    python api/modules/intent_router/training/eval_keyword_baseline.py
"""
import collections
import json
from pathlib import Path

DATASET = Path(__file__).resolve().parents[1] / "data" / "intent_dataset.json"

INTENT_MAPPINGS = {   # copied from the original service.py
    "finance": ["invoice", "total", "billing", "payment", "vat", "receipt"],
    "support": ["error", "bug", "help", "login", "broken", "issue", "crash"],
    "search": ["how to", "find", "document", "architecture", "query", "explain"],
    "orchestration": ["run", "execute", "trigger", "workflow", "automate", "sync"],
}


def old_router(query):
    q = query.lower()
    best, highest = "search", 0.50
    for intent, keywords in INTENT_MAPPINGS.items():
        matches = sum(1 for kw in keywords if kw in q)
        if matches > 0:
            score = min(0.98, 0.65 + matches * 0.12)
            if score > highest:
                highest, best = score, intent
    return best


samples = json.loads(DATASET.read_text(encoding="utf-8"))["samples"]
for name, ambiguous in (("clean", False), ("ambiguous", True)):
    rows = [s for s in samples if s["split"] == "test" and s["ambiguous"] == ambiguous]
    preds = [old_router(s["text"]) for s in rows]
    ok = sum(p == s["label"] for p, s in zip(preds, rows, strict=False))
    print(f"original keyword router, {name} test queries: {ok}/{len(rows)} = {ok / len(rows):.3f}")
    if not ambiguous:
        per = collections.defaultdict(lambda: [0, 0])
        for p, s in zip(preds, rows, strict=False):
            per[s["label"]][1] += 1
            per[s["label"]][0] += p == s["label"]
        print("  correct per class:", {k: f"{v[0]}/{v[1]}" for k, v in per.items()})
        print("  predicted distribution:", dict(collections.Counter(preds)))

