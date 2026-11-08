"""TF-IDF + Logistic Regression baseline for CTX-001. Never touches the test split."""
import json
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.pipeline import make_pipeline

SEED = 42
THRESHOLD = 0.60
path = sys.argv[1] if len(sys.argv) > 1 else "data/intent_dataset.json"
with open(path, encoding="utf-8") as f:
    samples = json.load(f)["samples"]


def split(name, ambiguous=None):
    rows = [s for s in samples if s["split"] == name
            and (ambiguous is None or s["ambiguous"] == ambiguous)]
    return [r["text"] for r in rows], [r["label"] for r in rows]


X_tr, y_tr = split("train")
X_val, y_val = split("validation", ambiguous=False)   # 30 clean queries
X_amb, y_amb = split("validation", ambiguous=True)    # 10 ambiguous queries

model = make_pipeline(
    TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
    LogisticRegression(max_iter=1000, C=10, random_state=SEED),
)
model.fit(X_tr, y_tr)
classes = list(model.classes_)
search_idx = classes.index("search")


def decide(X):
    proba = model.predict_proba(X)
    pred = proba.argmax(1)
    fallback = proba.max(1) < THRESHOLD
    final = np.where(fallback, search_idx, pred)
    return proba, [classes[i] for i in pred], [classes[i] for i in final], fallback


proba, pred, final, fb = decide(X_val)
print(f"clean val (n={len(y_val)})")
print(f"  argmax accuracy        : {accuracy_score(y_val, pred):.3f}")
print(f"  with 0.60 fallback     : {accuracy_score(y_val, final):.3f}")
print(f"  macro-F1 (with fallback): {f1_score(y_val, final, average='macro'):.3f}")
print(f"  fallback rate          : {fb.mean():.2f}   mean top-1 prob: {proba.max(1).mean():.2f}")
print(classification_report(y_val, final, zero_division=0))

proba, _, _, fb = decide(X_amb)
print(f"ambiguous val (n={len(y_amb)}): fallback rate {fb.mean():.2f}, "
      f"mean top-1 prob {proba.max(1).mean():.2f}")
