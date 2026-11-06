# ruff: noqa: B023, B905
import json
from pathlib import Path

ROOT = Path("data/sroie/extracted/sroie")
OUTPUT = Path("data/sroie/processed")
OUTPUT.mkdir(parents=True, exist_ok=True)
for split in ("train", "test"):
    records = []
    for annotation in sorted((ROOT / split / "tagged").glob("*.json")):
        data = json.loads(annotation.read_text(encoding="utf-8"))
        entities = {}
        current_label = None
        current_words = []
        def save_entity():
            if current_label and current_words:
                entities.setdefault(current_label, []).append(" ".join(current_words))
        for word, tag in zip(data["words"], data["labels"]):
            if tag.startswith("B-"):
                save_entity()
                current_label = tag[2:]
                current_words = [word]
            elif tag.startswith("I-") and current_label == tag[2:]:
                current_words.append(word)
            else:
                save_entity()
                current_label = None
                current_words = []
        save_entity()
        records.append({
            "document_id": annotation.stem,
            "words": data["words"],
            "bboxes": data["bbox"],
            "entities": {
                "vendor_name": entities.get("COMPANY", []),
                "date": entities.get("DATE", []),
                "address": entities.get("ADDRESS", []),
                "total": entities.get("TOTAL", [])
            }
        })
    (OUTPUT / f"{split}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8"
    )
    print(f"{split}: {len(records)} records saved")
print("Conversion complete.")

