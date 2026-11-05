"""Day 14, part 1: tuning experiments (9 runs) for CTX-001.

Varies: intra-op threads, max sequence length, batch size, FP32 vs INT8 (dynamic quantization).
Measures per run: latency on typical queries and on the worst case (a 10,000-character payload),
throughput, model size, and end-to-end accuracy on CLEAN validation queries (n=30, uses T and
the 0.60 fallback rule). The test split is never used.

Run from the repo root:
    python api/modules/intent_router/profiling/bench_experiments.py
Output: reports/bench_results.md and reports/bench_results.json
"""
import argparse
import json
import time

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from common import MODEL_DIR, REPORTS, hardware, load_samples, long_payload, percentiles
from modules.intent_router.service import softmax

FP32 = MODEL_DIR / "model.onnx"
INT8 = MODEL_DIR / "model.int8.onnx"
DEFAULT_THREADS = 4
EXPERIMENTS = [  # id, model, threads, max_len, batch
    ("E1", "fp32", DEFAULT_THREADS, 64, 1),     # production configuration (baseline)
    ("E2", "fp32", DEFAULT_THREADS, 128, 1),
    ("E3", "fp32", DEFAULT_THREADS, 256, 1),
    ("E4", "fp32", DEFAULT_THREADS, 64, 4),
    ("E5", "fp32", DEFAULT_THREADS, 64, 16),
    ("E6", "int8", DEFAULT_THREADS, 64, 1),
    ("E7", "int8", DEFAULT_THREADS, 256, 1),
    ("E8", "fp32", 1, 64, 1),
    ("E9", "fp32", 2, 64, 1),
]


def ensure_int8():
    if INT8.exists():
        return INT8
    try:
        from onnxruntime.quantization import QuantType, quantize_dynamic
        quantize_dynamic(str(FP32), str(INT8), weight_type=QuantType.QInt8)
        return INT8
    except Exception as e:  # needs `pip install onnx`
        print("INT8 quantization unavailable:", repr(e)[:200])
        return None


def make_session(path, threads):
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    opts.intra_op_num_threads = threads
    opts.inter_op_num_threads = 1
    return ort.InferenceSession(str(path), sess_options=opts, providers=["CPUExecutionProvider"])


def make_tokenizer(max_len):
    tk = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
    tk.enable_truncation(max_length=max_len)
    tk.enable_padding(pad_id=tk.token_to_id("[PAD]"), pad_token="[PAD]")   # needed for batch > 1
    return tk


def make_infer(session, tk, temperature):
    def infer(texts):
        enc = tk.encode_batch(texts)
        ids = np.asarray([e.ids for e in enc], dtype=np.int64)
        mask = np.asarray([e.attention_mask for e in enc], dtype=np.int64)
        logits = session.run(["logits"], {"input_ids": ids, "attention_mask": mask})[0]
        return np.stack([softmax(row, temperature) for row in logits])
    return infer


def time_calls(infer, pool, batch, n_iter):
    for i in range(20):                                                   # warm-up
        infer([pool[(i * batch + j) % len(pool)] for j in range(batch)])
    ms = []
    for i in range(n_iter):
        texts = [pool[(i * batch + j) % len(pool)] for j in range(batch)]
        t = time.perf_counter()
        infer(texts)
        ms.append((time.perf_counter() - t) * 1000)
    return percentiles(ms)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=300)
    args = ap.parse_args()

    cal = json.loads((MODEL_DIR / "calibration.json").read_text())
    T = float(cal["temperature"])
    labels_json = json.loads((MODEL_DIR / "labels.json").read_text())
    labels = [labels_json[str(i)] for i in range(len(labels_json))]
    clean = load_samples("validation", ambiguous=False)
    typical = [s["text"] for s in clean + load_samples("train")[:40]]
    worst = [long_payload()]
    int8_path = ensure_int8()

    rows = []
    for exp_id, kind, threads, max_len, batch in EXPERIMENTS:
        path = FP32 if kind == "fp32" else int8_path
        if path is None:
            print(f"{exp_id}: skipped (no INT8 model)")
            continue
        sess, tk = make_session(path, threads), make_tokenizer(max_len)
        infer = make_infer(sess, tk, T)
        n = args.iters if batch == 1 else max(50, args.iters // 3)
        typ, wst = time_calls(infer, typical, batch, n), time_calls(infer, worst, batch, n)
        # accuracy: one query at a time, same decision rule as the service
        correct, fallbacks = 0, 0
        for s in clean:
            p = infer([s["text"]])[0]
            fb = round(float(p.max()), 4) < 0.60
            pred = "search" if fb else labels[int(p.argmax())]
            correct += pred == s["label"]
            fallbacks += fb
        rows.append({"id": exp_id, "model": kind, "threads": threads, "max_len": max_len, "batch": batch,
                     "typical_p50": typ["p50"], "typical_p95": typ["p95"],
                     "worst_p50": wst["p50"], "worst_p95": wst["p95"],
                     "items_per_s": batch / (typ["p50"] / 1000),
                     "size_mb": path.stat().st_size / 1e6,
                     "clean_acc": correct / len(clean), "fallback_rate": fallbacks / len(clean)})
        r = rows[-1]
        print(f"{exp_id} {kind} t={threads} len={max_len} b={batch}: typical p50 {r['typical_p50']:.1f} / p95 "
              f"{r['typical_p95']:.1f} ms | worst p50 {r['worst_p50']:.1f} / p95 {r['worst_p95']:.1f} ms | acc {r['clean_acc']:.3f}")

    hdr = ("| ID | model | threads | max_len | batch | typical p50 / p95 (ms) | worst-case p50 / p95 (ms) | "
           "items/s | size MB | clean acc | fallback |\n|---|---|---|---|---|---|---|---|---|---|---|\n")
    body = "".join(
        f"| {r['id']} | {r['model']} | {r['threads']} | {r['max_len']} | {r['batch']} | "
        f"{r['typical_p50']:.2f} / {r['typical_p95']:.2f} | {r['worst_p50']:.2f} / {r['worst_p95']:.2f} | "
        f"{r['items_per_s']:.0f} | {r['size_mb']:.0f} | {r['clean_acc']:.3f} | {r['fallback_rate']:.2f} |\n"
        for r in rows)
    md = (f"# Benchmark results\n\nHardware: `{json.dumps(hardware())}`\n\nTemperature T = {T}. "
          f"'typical' = dataset queries, 'worst-case' = one 10,000-character payload. Batch rows report latency per CALL.\n\n"
          + hdr + body)
    (REPORTS / "bench_results.md").write_text(md, encoding="utf-8")
    (REPORTS / "bench_results.json").write_text(json.dumps({"hardware": hardware(), "T": T, "runs": rows}, indent=2), encoding="utf-8")
    print("\n" + hdr + body)


if __name__ == "__main__":
    main()
