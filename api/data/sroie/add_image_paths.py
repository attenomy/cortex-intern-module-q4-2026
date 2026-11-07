import json
from pathlib import Path

root = Path("data/sroie/extracted/sroie")
output = Path("data/sroie/processed")
for split in ("train", "test"):
    source = output / f"{split}.jsonl"
    records = []
    for line in source.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        record["image_path"] = str(
            (root / split / "images" / f"{record['document_id']}.jpg").resolve()
        )
        records.append(record)
    source.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
        encoding="utf-8"
    )
    print(split, len(records), "records updated")
print("Image paths added.")
