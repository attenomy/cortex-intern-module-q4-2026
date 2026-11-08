"""Day 15: final evaluation on the TEST split (CTX-001).

Use this ONCE, after model, temperature and every setting are frozen. Never change anything because of
what it prints (that would turn the test split into a tuning set). Run it with --final to confirm.

What it does
  * runs every test query through the real service (`SemanticRouter.route_query`: tokenizer, ONNX model,
    temperature, 0.60 fallback rule), so the numbers describe what production would do
  * clean test queries (n=30): accuracy (argmax and end-to-end), macro-F1, per-class precision/recall,
    95% Wilson interval, confusion matrix
  * ambiguous test queries (n=10, the mixed-intent group of support and orchestration): confidence and
    fallback behaviour, compared with the clean queries
  * the same numbers for the TF-IDF + Logistic Regression baseline trained on the train split
  * a list of every clean-test error and every fallback (the material for the error analysis)

Run from the repo root:
    python api/modules/intent_router/training/evaluate_test.py --final
Output: reports/test_evaluation.md, reports/test_evaluation.json, reports/figures/confusion_matrix.png
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

MODULE_DIR = Path(__file__).resolve().parents[1]
API_DIR = MODULE_DIR.parents[1]
sys.path.insert(0, str(API_DIR))
REPORTS = MODULE_DIR / "reports"
FIGURES = REPORTS / "figures"
THRESHOLD = 0.60


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (c - h, c + h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="confirm that the configuration is frozen")
    args = ap.parse_args()
    if not args.final:
        sys.exit("This evaluates the TEST split. Run it once, after everything is frozen: add --final")

    from modules.intent_router.service import SemanticRouter
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, confusion_matrix, f1_score
    from sklearn.pipeline import make_pipeline

    doc = json.loads((MODULE_DIR / "data" / "intent_dataset.json").read_text(encoding="utf-8"))
    labels = doc["meta"]["labels"]
    all_samples = doc["samples"]
    train = [s for s in all_samples if s["split"] == "train"]
    clean = [s for s in all_samples if s["split"] == "test" and not s["ambiguous"]]
    amb = [s for s in all_samples if s["split"] == "test" and s["ambiguous"]]

    router = SemanticRouter()
    router.load()

    def run_router(rows):
        out = []
        for s in rows:
            r = router.route_query(s["text"], max_candidates=3)
            out.append({"id": s["id"], "text": s["text"], "true": s["label"], "argmax": r["top_k"][0]["intent_category"],
                        "final": r["intent_category"], "fallback": r["fallback_triggered"], "confidence": r["confidence"],
                        "top_k": [(c["intent_category"], c["confidence"]) for c in r["top_k"]]})
        return out

    res_clean, res_amb = run_router(clean), run_router(amb)

    def metrics(res, key):
        y = [r["true"] for r in res]
        p = [r[key] for r in res]
        k = sum(a == b for a, b in zip(y, p, strict=False))
        return {"accuracy": k / len(res), "correct": k, "n": len(res),
                "wilson95": wilson(k, len(res)), "macro_f1": f1_score(y, p, labels=labels, average="macro", zero_division=0)}

    m_argmax, m_final = metrics(res_clean, "argmax"), metrics(res_clean, "final")
    y_true = [r["true"] for r in res_clean]
    y_pred = [r["final"] for r in res_clean]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    report_txt = classification_report(y_true, y_pred, labels=labels, zero_division=0)

    # TF-IDF + LR baseline, same decision rule
    base = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True), LogisticRegression(max_iter=1000, C=10, random_state=42))
    base.fit([s["text"] for s in train], [s["label"] for s in train])
    proba = base.predict_proba([s["text"] for s in clean])
    cls = list(base.classes_)
    b_arg = [cls[i] for i in proba.argmax(1)]
    b_fin = ["search" if proba[i].max() < THRESHOLD else b_arg[i] for i in range(len(clean))]
    kb_arg, kb_fin = sum(a == b for a, b in zip(y_true, b_arg, strict=False)), sum(a == b for a, b in zip(y_true, b_fin, strict=False))
    base_res = {"argmax_accuracy": kb_arg / len(clean), "end_to_end_accuracy": kb_fin / len(clean),
                "macro_f1": f1_score(y_true, b_fin, labels=labels, average="macro", zero_division=0),
                "fallback_rate": float(np.mean(proba.max(1) < THRESHOLD))}

    errors = [r for r in res_clean if r["final"] != r["true"]]
    fallbacks = [r for r in res_clean if r["fallback"]]
    conf_clean = float(np.mean([r["confidence"] for r in res_clean]))
    conf_amb = float(np.mean([r["confidence"] for r in res_amb]))
    summary = {
        "temperature": router.temperature, "n_clean": len(res_clean), "n_ambiguous": len(res_amb),
        "minilm_clean": {"argmax": m_argmax, "end_to_end": m_final, "fallback_rate": float(np.mean([r["fallback"] for r in res_clean])),
                         "mean_confidence": conf_clean},
        "tfidf_baseline_clean": base_res,
        "ambiguous": {"fallback_rate": float(np.mean([r["fallback"] for r in res_amb])), "mean_confidence": conf_amb,
                      "end_to_end_accuracy_vs_main_intent": float(np.mean([r["final"] == r["true"] for r in res_amb]))},
        "confusion_matrix": {"labels": labels, "rows_true_cols_pred": cm.tolist()},
    }
    REPORTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    (REPORTS / "test_evaluation.json").write_text(json.dumps({"summary": summary, "clean": res_clean, "ambiguous": res_amb}, indent=2), encoding="utf-8")

    def fmt_k(r):
        return ", ".join(f"{c} {p:.2f}" for c, p in r["top_k"])
    lines = ["# Test split evaluation (run once, configuration frozen)\n",
             f"Temperature T = {router.temperature}; fallback rule: top probability < 0.60 routes to `search`.\n",
             f"## Clean test queries (n={len(res_clean)})\n",
             "| model | argmax acc | end-to-end acc (with fallback) | 95% interval | macro-F1 | fallback rate |\n|---|---|---|---|---|---|\n",
             f"| fine-tuned MiniLM (ONNX) | {m_argmax['accuracy']:.3f} | {m_final['accuracy']:.3f} ({m_final['correct']}/{m_final['n']}) | "
             f"{m_final['wilson95'][0]:.2f} to {m_final['wilson95'][1]:.2f} | {m_final['macro_f1']:.3f} | {summary['minilm_clean']['fallback_rate']:.2f} |\n",
             f"| TF-IDF + Logistic Regression | {base_res['argmax_accuracy']:.3f} | {base_res['end_to_end_accuracy']:.3f} | | "
             f"{base_res['macro_f1']:.3f} | {base_res['fallback_rate']:.2f} |\n",
             "\nPer-class (MiniLM, end to end):\n\n```\n" + report_txt + "```\n",
             "Confusion matrix (rows = true, columns = routed; the `search` column includes fallbacks):\n\n```\n"
             + "            " + " ".join(f"{lbl[:6]:>7}" for lbl in labels) + "\n"
             + "\n".join(f"{labels[i]:<12}" + " ".join(f"{v:>7}" for v in row) for i, row in enumerate(cm.tolist())) + "\n```\n",
             f"\n## Errors on clean test queries ({len(errors)})\n"]
    lines += [f"- `{r['text']}`: true **{r['true']}**, routed **{r['final']}** (fallback: {r['fallback']}), "
              f"confidence {r['confidence']:.2f}; top-3: {fmt_k(r)}\n" for r in errors] or ["- none\n"]
    lines += [f"\n## Fallbacks on clean test queries ({len(fallbacks)})\n"]
    lines += [f"- `{r['text']}` (true {r['true']}): confidence {r['confidence']:.2f}; top-3: {fmt_k(r)}\n" for r in fallbacks] or ["- none\n"]
    lines += [f"\n## Ambiguous (mixed-intent) test queries (n={len(res_amb)})\n",
              f"Mean confidence {conf_amb:.2f} vs {conf_clean:.2f} on clean queries; fallback rate {summary['ambiguous']['fallback_rate']:.2f}.\n\n"]
    lines += [f"- `{r['text']}` (main intent {r['true']}): routed {r['final']}, confidence {r['confidence']:.2f}; top-3: {fmt_k(r)}\n" for r in res_amb]
    (REPORTS / "test_evaluation.md").write_text("".join(lines), encoding="utf-8")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from sklearn.metrics import ConfusionMatrixDisplay
        fig, ax = plt.subplots(figsize=(5.5, 5))
        ConfusionMatrixDisplay(cm, display_labels=labels).plot(ax=ax, xticks_rotation=30, colorbar=False)
        ax.set_title(f"Test split, clean queries (n={len(res_clean)})")
        fig.tight_layout()
        fig.savefig(FIGURES / "confusion_matrix.png", dpi=150)
    except ImportError:
        print("matplotlib not installed: skipping confusion_matrix.png")

    print("".join(lines))


if __name__ == "__main__":
    main()
