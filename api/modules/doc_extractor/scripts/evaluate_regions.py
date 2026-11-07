import json
import time
import statistics
from pathlib import Path
from collections import Counter
from PIL import Image
from modules.doc_extractor.ocr import TesseractOCR
from modules.doc_extractor.region_detector import detect_layout_regions
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "real_sroie" / "manifest.jsonl"
REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)
ocr = TesseractOCR()
results = []
errors = []
region_counts = Counter()
latencies = []
with MANIFEST.open(encoding="utf-8") as file:
    records = [
        json.loads(line)
        for line in file
        if line.strip()
    ]
test_records = [r for r in records if r.get("split") == "test"]
for index, record in enumerate(test_records, 1):
    image_path = ROOT / record["image_path"]
    try:
        with Image.open(image_path) as source:
            image = source.convert("RGB")
        start = time.perf_counter()
        ocr_data = ocr.extract_text_with_confidence(image)
        regions = detect_layout_regions(
            ocr_data.get("words", []),
            image.width,
            image.height,
        )
        elapsed = (time.perf_counter() - start) * 1000
        names = [r.region_type.value for r in regions]
        region_counts.update(names)
        latencies.append(elapsed)
        results.append({
            "document_id": record["document_id"],
            "regions": names,
            "word_count": len(ocr_data.get("words", [])),
            "latency_ms": round(elapsed, 2),
        })
    except Exception as exc:
        errors.append({
            "document_id": record.get("document_id"),
            "error": str(exc),
        })
    if index % 25 == 0:
        print(f"Processed {index}/{len(test_records)}")
total = len(test_records)
successful = len(results)
summary = {
    "dataset": "SROIE",
    "split": "test",
    "total_documents": total,
    "processed": successful,
    "errors": len(errors),
    "region_detection_counts": dict(region_counts),
    "detection_rate": {
        name: round(
            sum(name in r["regions"] for r in results) / successful * 100, 2
        ) if successful else 0
        for name in ["header", "line_item_table", "totals_block"]
    },
    "latency_ms": {
        "median": round(statistics.median(latencies), 2) if latencies else None,
        "p95": round(sorted(latencies)[int(0.95 * (len(latencies)-1))], 2) if latencies else None,
        "mean": round(statistics.mean(latencies), 2) if latencies else None,
    },
    "errors_detail": errors,
    "document_results": results,
    "evaluation_note": (
        "Heuristic candidate detection only. SROIE provides word-level "
        "annotations, not major-region ground truth. IoU accuracy is not "
        "claimed or calculated."
    ),
}
json_path = REPORT_DIR / "region_detection_evaluation.json"
json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
md = [
    "# SROIE Region Detection Evaluation",
    "",
    f"- Test documents: {total}",
    f"- Successfully processed: {successful}",
    f"- Errors: {len(errors)}",
    "",
    "## Region detection rate",
]
for name, rate in summary["detection_rate"].items():
    md.append(f"- {name}: {rate}%")
md += [
    "",
    "## Latency",
    f"- Median: {summary['latency_ms']['median']} ms",
    f"- P95: {summary['latency_ms']['p95']} ms",
    f"- Mean: {summary['latency_ms']['mean']} ms",
    "",
    "## Limitation",
    summary["evaluation_note"],
]
(REPORT_DIR / "region_detection_evaluation.md").write_text(
    "\n".join(md), encoding="utf-8"
)
print(json.dumps({
    "processed": successful,
    "errors": len(errors),
    "detection_rate": summary["detection_rate"],
    "latency_ms": summary["latency_ms"],
    "reports": [
        str(json_path),
        str(REPORT_DIR / "region_detection_evaluation.md"),
    ],
}, indent=2))
