import json
import sys
import time
from collections import Counter
from pathlib import Path
import torch
from PIL import Image
from torchvision import transforms
API_ROOT = Path.cwd()
MODULE_ROOT = API_ROOT / "modules" / "doc_extractor"
sys.path.insert(0, str(API_ROOT))
from modules.doc_extractor.layout_classifier import (
    DOCUMENT_CLASSES,
    build_classifier,
    predict_document,
)
MANIFEST = MODULE_ROOT / "data" / "real_sroie" / "manifest.jsonl"
MODEL_PATH = MODULE_ROOT / "models" / "document_classifier.pth"
REPORT_PATH = MODULE_ROOT / "reports" / "sroie_real_test_evaluation.md"
device = torch.device("cpu")
model = build_classifier(pretrained=False)
state = torch.load(MODEL_PATH, map_location=device, weights_only=True)
model.load_state_dict(state, strict=True)
model.eval()
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])
records = [
    json.loads(line)
    for line in MANIFEST.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
records = [
    r for r in records
    if r.get("split") == "test" and r.get("category") == "receipt"
]
if not records:
    raise RuntimeError("No held-out SROIE receipt test records found.")
correct = 0
failures = []
predictions = Counter()
latencies = []
with torch.inference_mode():
    # Warm-up
    dummy = torch.zeros(1, 3, 224, 224)
    for _ in range(5):
        model(dummy)
    for record in records:
        image_path = MODULE_ROOT / Path(record["image_path"])
        try:
            with Image.open(image_path) as image:
                tensor = preprocess(image.convert("RGB")).unsqueeze(0)
            start = time.perf_counter()
            prediction = predict_document(model, tensor)
            latencies.append((time.perf_counter() - start) * 1000)
            predicted = prediction["document_type"]
            predictions[predicted] += 1
            if predicted == "receipt":
                correct += 1
        except Exception as exc:
            failures.append({
                "document_id": record.get("document_id"),
                "error": str(exc),
            })
evaluated = len(latencies)
accuracy = correct / evaluated if evaluated else 0.0
sorted_latencies = sorted(latencies)
def percentile(values, p):
    if not values:
        return 0.0
    index = min(len(values) - 1, int((len(values) - 1) * p))
    return values[index]
median_ms = percentile(sorted_latencies, 0.50)
p95_ms = percentile(sorted_latencies, 0.95)
report = [
    "# SROIE Real-World Receipt Classification Evaluation",
    "",
    "## Dataset",
    "- Source: SROIE annotated receipt dataset",
    f"- Held-out test records: {len(records)}",
    f"- Successfully evaluated: {evaluated}",
    f"- Evaluation failures: {len(failures)}",
    "- Ground-truth class: receipt",
    "- Model: MobileNetV3-Small, four output classes",
    "",
    "## Results",
    f"- Receipt recall / accuracy: {accuracy:.4f}",
    f"- Correct receipt predictions: {correct}/{evaluated}",
    f"- Median model inference latency: {median_ms:.2f} ms",
    f"- p95 model inference latency: {p95_ms:.2f} ms",
    "",
    "## Predicted Class Distribution",
    "| Predicted class | Count |",
    "|---|---:|",
]
for cls in DOCUMENT_CLASSES:
    report.append(f"| {cls} | {predictions[cls]} |")
report.extend([
    "",
    "## Limitations",
    "- This is a receipt-only evaluation, not a four-class benchmark.",
    "- Accuracy here is receipt recall on the SROIE test split.",
    "- Latency measures model inference only, excluding image decoding and OCR.",
    "- Results do not establish the four-class Macro F1 acceptance target.",
    "",
    "## Evaluation Failures",
])
if failures:
    for failure in failures:
        report.append(
            f"- {failure['document_id']}: {failure['error']}"
        )
else:
    report.append("- None")
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
print("SROIE EVALUATION COMPLETE")
print("Evaluated:", evaluated, "/", len(records))
print("Receipt recall:", round(accuracy, 4))
print("Predictions:", dict(predictions))
print("Median inference:", round(median_ms, 2), "ms")
print("P95 inference:", round(p95_ms, 2), "ms")
print("Failures:", len(failures))
print("Report:", REPORT_PATH)
