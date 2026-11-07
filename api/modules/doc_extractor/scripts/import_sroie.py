import json
import hashlib
import shutil
from pathlib import Path
from collections import Counter
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent.parent / "data" / "sroie" / "processed"
OUTPUT = ROOT / "data" / "real_sroie"
REPORT = ROOT / "reports" / "sroie_import_report.md"
def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    counts = Counter()
    records = []
    missing = 0
    duplicates = 0
    for split in ("train", "test"):
        source_file = SOURCE / f"{split}.jsonl"
        if not source_file.exists():
            print(f"Missing source: {source_file}")
            continue
        with source_file.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                item = json.loads(line)
                image = Path(item.get("image_path", ""))
                if not image.is_file():
                    missing += 1
                    continue
                digest = hashlib.md5(image.read_bytes()).hexdigest()
                if digest in seen:
                    duplicates += 1
                    continue
                seen.add(digest)
                destination = OUTPUT / split / "receipt" / f"{item['document_id']}{image.suffix.lower()}"
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(image, destination)
                record = {
                    "document_id": item["document_id"],
                    "category": "receipt",
                    "split": split,
                    "image_path": str(destination.relative_to(ROOT)),
                    "md5": digest,
                    "provenance": "SROIE - real annotated dataset",
                    "entities": item.get("entities", {}),
                    "words": item.get("words", []),
                    "bboxes": item.get("bboxes", [])
                }
                records.append(record)
                counts[split] += 1
    manifest = OUTPUT / "manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    report = [
        "# SROIE Real Dataset Import",
        "",
        "- Source: existing processed SROIE annotations",
        "- Class imported: receipt",
        "- Provenance: real SROIE dataset",
        "- Synthetic samples included: No",
        f"- Train images: {counts['train']}",
        f"- Test images: {counts['test']}",
        f"- Missing images: {missing}",
        f"- Duplicate images skipped: {duplicates}",
        f"- Total imported: {len(records)}",
        "",
        "Note: SROIE does not provide contract or purchase-order labels.",
        "This dataset must not be represented as a four-class benchmark."
    ]
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print("\nSROIE IMPORT COMPLETE")
    print(f"Train: {counts['train']} | Test: {counts['test']}")
    print(f"Imported: {len(records)} | Missing: {missing} | Duplicates: {duplicates}")
    print(f"Manifest: {manifest}")
    print(f"Report: {REPORT}")
if __name__ == "__main__":
    main()
