import json
import statistics
import time
import cProfile
import tracemalloc
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps
import pytesseract
from pytesseract import Output
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "real_sroie" / "manifest.jsonl"
REPORT = ROOT / "reports"
REPORT.mkdir(exist_ok=True)
records = [
    json.loads(line)
    for line in MANIFEST.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
records = [r for r in records if r["split"] == "test"][:30]
images = []
for record in records:
    path = ROOT / record["image_path"]
    if path.exists():
        with Image.open(path) as image:
            images.append(image.convert("RGB"))
if not images:
    raise RuntimeError("No SROIE test images found.")
def percentile(values, p=0.95):
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * p)))
    return ordered[index]
def run_ocr(image, config="--oem 3 --psm 6"):
    return pytesseract.image_to_data(
        image, config=config, output_type=Output.DICT
    )
def prepare_image(image, resolution, denoise):
    processed = image.copy()
    if denoise == "median_3x3":
        processed = processed.filter(ImageFilter.MedianFilter(size=3))
    elif denoise == "median_5x5":
        processed = processed.filter(ImageFilter.MedianFilter(size=5))
    return ImageOps.pad(
        processed,
        (resolution, resolution),
        method=Image.Resampling.LANCZOS,
        color="white"
    )
results = []
# Existing six OCR PSM/DPI experiments
psm_configs = {
    "psm_3": "--oem 3 --psm 3",
    "psm_4": "--oem 3 --psm 4",
    "psm_6": "--oem 3 --psm 6",
    "psm_11": "--oem 3 --psm 11",
    "psm_12": "--oem 3 --psm 12",
    "psm_6_dpi300": "--oem 3 --psm 6 -c user_defined_dpi=300",
}
for name, config in psm_configs.items():
    timings, word_counts = [], []
    for image in images:
        start = time.perf_counter()
        data = run_ocr(image, config)
        timings.append((time.perf_counter() - start) * 1000)
        word_counts.append(sum(
            bool(word.strip()) for word in data["text"]
        ))
    results.append({
        "experiment": name,
        "config": config,
        "images": len(images),
        "median_ms": round(statistics.median(timings), 2),
        "p95_ms": round(percentile(timings), 2),
        "mean_words": round(statistics.mean(word_counts), 2),
    })
    print(results[-1])
# Requested 18-configuration tuning matrix
for resolution in (512, 1024):
    for threshold in (50, 70, 85):
        for denoise in ("none", "median_3x3", "median_5x5"):
            name = f"r{resolution}_conf{threshold}_{denoise}"
            timings, accepted_counts, raw_counts = [], [], []
            for original in images:
                image = prepare_image(original, resolution, denoise)
                start = time.perf_counter()
                data = run_ocr(image, "--oem 3 --psm 6")
                timings.append((time.perf_counter() - start) * 1000)
                accepted = 0
                raw = 0
                for word, confidence in zip(data["text"], data["conf"]):
                    if not word.strip():
                        continue
                    try:
                        confidence = float(confidence)
                    except (ValueError, TypeError):
                        continue
                    if confidence < 0:
                        continue
                    raw += 1
                    if confidence >= threshold:
                        accepted += 1
                raw_counts.append(raw)
                accepted_counts.append(accepted)
            result = {
                "experiment": name,
                "resolution": f"{resolution}x{resolution}",
                "confidence_threshold": threshold / 100,
                "denoise": denoise,
                "threshold_stage": "post_ocr_word_filter",
                "images": len(images),
                "median_ms": round(statistics.median(timings), 2),
                "p95_ms": round(percentile(timings), 2),
                "mean_raw_words": round(statistics.mean(raw_counts), 2),
                "mean_accepted_words": round(
                    statistics.mean(accepted_counts), 2
                ),
            }
            results.append(result)
            print(result)
(REPORT / "tuning_experiments.json").write_text(
    json.dumps(results, indent=2), encoding="utf-8"
)
with (REPORT / "tuning_experiments.md").open("w", encoding="utf-8") as f:
    f.write("# OCR Tuning Experiments\n\n")
    f.write(f"Dataset: SROIE test split, {len(images)} images.\n\n")
    f.write("Confidence thresholds are applied after OCR to filter words; ")
    f.write("they do not change Tesseract inference itself.\n\n")
    f.write("| Experiment | Median ms | P95 ms | Mean accepted words |\n")
    f.write("|---|---:|---:|---:|\n")
    for r in results:
        words = r.get("mean_accepted_words", r.get("mean_words", 0))
        f.write(
            f"| {r['experiment']} | {r['median_ms']} | "
            f"{r['p95_ms']} | {words} |\n"
        )
# Profile baseline OCR separately
baseline = "--oem 3 --psm 6"
tracemalloc.start()
profiler = cProfile.Profile()
profiler.enable()
for image in images:
    run_ocr(image, baseline)
profiler.disable()
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
profiler.dump_stats(str(REPORT / "ocr_profile.prof"))
(REPORT / "memory_profile.json").write_text(
    json.dumps({
        "images": len(images),
        "python_current_mb": round(current / 1024 / 1024, 2),
        "python_peak_mb": round(peak / 1024 / 1024, 2),
        "note": "Python allocations only; Tesseract subprocess memory excluded."
    }, indent=2),
    encoding="utf-8"
)
print(f"\nBenchmark complete: {len(results)} experiments")
print("Images:", len(images))
print("Reports:", REPORT)
