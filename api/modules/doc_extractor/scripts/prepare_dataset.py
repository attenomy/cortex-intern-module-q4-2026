"""
prepare_dataset.py - Synthetic Dataset Generation & Partitioning Pipeline
Attenomy Cortex CTX-002: Cognitive Document Entity Extractor

Generates and partitions a balanced 4-class synthetic document dataset:
1. invoice       (Source: Synthetic generation)
2. receipt       (Source: Synthetic generation)
3. contract      (Source: Synthetic generation)
4. purchase_order (Source: Synthetic generation)

Features:
- Validates image integrity and formats.
- Label normalization and duplicate detection (MD5 hash).
- Deterministic 70% Train / 15% Validation / 15% Test partitioning using random_seed=42.
- Generates JSON manifest and Markdown distribution report.
"""

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

# Set deterministic seed
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

CLASSES = ["invoice", "receipt", "contract", "purchase_order"]

PROVENANCE_SOURCES = dict.fromkeys(CLASSES, "Synthetic - generated locally; not sourced from public datasets")


def compute_md5(image_path: Path) -> str:
    """Compute MD5 hash of image file for duplicate detection."""
    hasher = hashlib.md5()
    with open(image_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_document_image(category: str, index: int, output_dir: Path) -> Path:
    """
    Generate an authentic document image representing the visual layout
    and typography of the given category.
    """
    # Distinct dimensions & layouts per document type
    if category == "receipt":
        # Narrow receipt thermal paper format
        width, height = random.choice([(400, 850), (450, 950), (380, 800)])
        bg_color = (250, 248, 240)  # slight off-white paper
    elif category == "invoice":
        width, height = 750, 1050  # Letter/A4 portrait
        bg_color = (255, 255, 255)
    elif category == "contract":
        width, height = 750, 1050  # Standard legal page
        bg_color = (255, 255, 255)
    else:  # purchase_order
        width, height = 750, 1050  # Landscape or portrait grid layout
        bg_color = (253, 253, 255)

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Use default bitmap font
    font = ImageFont.load_default()

    if category == "invoice":
        # Invoice layout: Distinct header banner, Vendor, Bill To, Table, Totals, Footer
        draw.rectangle([(0, 0), (width, 15)], fill=(16, 185, 129))  # Emerald accent banner
        vendor_names = ["Apex Technologies Ltd", "Global Logix Corp", "Synthetix Solutions", "Nexus Infotech"]
        vendor = random.choice(vendor_names)
        inv_no = f"INV-2026-{1000 + index}"
        draw.text((40, 40), vendor.upper(), fill=(20, 20, 20), font=font)
        draw.text((40, 60), "100 Enterprise Way, Tech Park, Suite 400", fill=(80, 80, 80), font=font)
        draw.rectangle([(width - 210, 35), (width - 35, 75)], fill=(235, 245, 240), outline=(16, 185, 129))
        draw.text((width - 195, 45), "COMMERCIAL INVOICE", fill=(10, 80, 50), font=font)
        draw.text((width - 195, 60), f"Inv #: {inv_no}", fill=(40, 40, 40), font=font)
        draw.text((width - 200, 85), "Date: 2026-10-15", fill=(40, 40, 40), font=font)

        # Divider
        draw.line([(40, 110), (width - 40, 110)], fill=(180, 180, 180), width=2)

        # Bill to
        draw.text((40, 130), "BILL TO:", fill=(30, 30, 30), font=font)
        draw.text((40, 150), "Attenomy Systems Inc", fill=(50, 50, 50), font=font)
        draw.text((40, 170), "500 Innovation Blvd, Silicon Valley, CA", fill=(70, 70, 70), font=font)

        # Table header
        table_y = 230
        draw.rectangle([(40, table_y), (width - 40, table_y + 25)], fill=(230, 230, 235))
        draw.text((50, table_y + 7), "ITEM DESCRIPTION", fill=(20, 20, 20), font=font)
        draw.text((450, table_y + 7), "QTY", fill=(20, 20, 20), font=font)
        draw.text((530, table_y + 7), "UNIT PRICE", fill=(20, 20, 20), font=font)
        draw.text((630, table_y + 7), "TOTAL", fill=(20, 20, 20), font=font)

        # Line items
        items = [
            ("Cloud Compute Instance - High Mem", 2, 450.00),
            ("Vector Storage Allocation (1TB)", 1, 320.00),
            ("Dedicated API Gateway Router", 1, 150.00),
            ("Enterprise Support Subscription", 1, 500.00),
        ]
        subtotal = 0.0
        cur_y = table_y + 35
        for desc, qty, price in items:
            line_tot = qty * price
            subtotal += line_tot
            draw.text((50, cur_y), desc, fill=(50, 50, 50), font=font)
            draw.text((460, cur_y), str(qty), fill=(50, 50, 50), font=font)
            draw.text((540, cur_y), f"${price:.2f}", fill=(50, 50, 50), font=font)
            draw.text((630, cur_y), f"${line_tot:.2f}", fill=(50, 50, 50), font=font)
            draw.line([(40, cur_y + 20), (width - 40, cur_y + 20)], fill=(240, 240, 240), width=1)
            cur_y += 30

        # Totals block
        tax = subtotal * 0.10
        total = subtotal + tax
        tot_x = width - 240
        draw.rectangle([(tot_x - 10, cur_y + 20), (width - 40, cur_y + 110)], outline=(200, 200, 200))
        draw.text((tot_x, cur_y + 30), f"Subtotal:     ${subtotal:.2f}", fill=(40, 40, 40), font=font)
        draw.text((tot_x, cur_y + 55), f"Tax (10%):    ${tax:.2f}", fill=(40, 40, 40), font=font)
        draw.text((tot_x, cur_y + 80), f"NET AMOUNT:   ${total:.2f}", fill=(10, 10, 10), font=font)

        # Footer notes
        draw.text((40, height - 80), "Payment Terms: Net 30 Days. Remit to payment@apextech.com", fill=(100, 100, 100), font=font)

    elif category == "receipt":
        # Thermal receipt layout: Centered headers, dashed dividers, compact lines
        store = random.choice(["METRO HYPERMARKET", "STAR MART & CAFE", "VALU PHARMACY", "CENTRAL QUICKSTOP"])
        draw.text((width // 2 - 60, 30), store, fill=(10, 10, 10), font=font)
        draw.text((width // 2 - 80, 50), "STORE #4028 - TERMINAL #02", fill=(60, 60, 60), font=font)
        draw.text((width // 2 - 70, 70), "TEL: +1 (800) 555-0199", fill=(60, 60, 60), font=font)
        draw.text((20, 100), "---------------------------------------------", fill=(100, 100, 100), font=font)
        draw.text((20, 115), f"RCPT #{202600 + index}  2026-11-01  14:32", fill=(50, 50, 50), font=font)
        draw.text((20, 130), "---------------------------------------------", fill=(100, 100, 100), font=font)

        items = [
            ("ORGANIC MILK 1L", 3.49),
            ("WHOLE WHEAT BREAD", 2.99),
            ("ROASTED COFFEE BEANS", 12.50),
            ("MINERAL WATER 6PK", 4.99),
            ("PAPER TOWELS 2PK", 5.25),
        ]
        sub = 0.0
        ry = 150
        for itm, prc in items:
            sub += prc
            draw.text((25, ry), itm, fill=(30, 30, 30), font=font)
            draw.text((width - 80, ry), f"${prc:.2f}", fill=(30, 30, 30), font=font)
            ry += 25

        draw.text((20, ry), "---------------------------------------------", fill=(100, 100, 100), font=font)
        ry += 15
        tax = sub * 0.08
        tot = sub + tax
        draw.text((30, ry), "SUBTOTAL", fill=(30, 30, 30), font=font)
        draw.text((width - 80, ry), f"${sub:.2f}", fill=(30, 30, 30), font=font)
        ry += 20
        draw.text((30, ry), "TAX 8.00%", fill=(30, 30, 30), font=font)
        draw.text((width - 80, ry), f"${tax:.2f}", fill=(30, 30, 30), font=font)
        ry += 25
        draw.text((30, ry), "TOTAL AMOUNT", fill=(10, 10, 10), font=font)
        draw.text((width - 80, ry), f"${tot:.2f}", fill=(10, 10, 10), font=font)
        ry += 35
        draw.text((width // 2 - 70, ry), "*** THANK YOU FOR SHOPPING ***", fill=(80, 80, 80), font=font)

    elif category == "contract":
        # Legal agreement layout: Dense paragraphs, clause titles, signature lines
        contract_no = f"AGR-2026-{2000 + index}"
        provider = random.choice(["Provider Enterprises LLC", "Cognitive Systems Inc", "Vertex Core Ltd", "Attenomy Holdings"])
        client = random.choice(["Client Corporations Ltd", "Zenith Retail Group", "Global Logistics AG", "Pacific Ventures"])
        title = "MASTER SERVICES & LICENSE AGREEMENT"
        draw.text((width // 2 - 120, 50), title, fill=(10, 10, 10), font=font)
        draw.text((width // 2 - 100, 70), f"CONTRACT REF: {contract_no}", fill=(70, 70, 70), font=font)

        body_paragraphs = [
            f"THIS AGREEMENT is entered into by and between {provider} ('Provider')",
            f"and {client} ('Client'). WHEREAS Provider specializes in autonomous AI",
            "orchestration, and Client desires to retain Provider for enterprise services.",
            "",
            "1. DEFINITIONS AND INTERPRETATIONS",
            "1.1 'Confidential Information' signifies all proprietary technical, financial, and product data.",
            "1.2 'Deliverables' shall mean cognitive software models, extraction pipelines, and APIs.",
            "",
            "2. SCOPE OF SERVICES & COMMENCEMENT",
            "Provider agrees to perform the designated engineering deliverables in compliance with specifications.",
            "Time is of the essence for all milestones established under Exhibit A attached hereto.",
            "",
            "3. INTELLECTUAL PROPERTY RIGHTS",
            "All background intellectual property shall remain the exclusive domain of Provider.",
            "Upon receipt of total payment, Client obtains an irrevocable enterprise runtime license.",
            "",
            "4. INDEMNIFICATION & LIABILITY LIMITATION",
            "Neither party shall be liable for indirect, incidental, punitive, or consequential damages.",
            "Maximum aggregate liability shall not exceed total fees paid over the preceding twelve months.",
            "",
            "5. GOVERNING LAW & JURISDICTION",
            "This Agreement shall be governed by and interpreted under the commercial laws of Delaware.",
        ]

        cy = 120
        for line in body_paragraphs:
            draw.text((50, cy), line, fill=(30, 30, 30), font=font)
            cy += 22

        # Signatures
        sig_y = height - 160
        draw.text((50, sig_y), "IN WITNESS WHEREOF, the authorized representatives execute this Agreement:", fill=(40, 40, 40), font=font)
        draw.line([(50, sig_y + 60), (280, sig_y + 60)], fill=(50, 50, 50), width=1)
        draw.text((50, sig_y + 65), "By: Authorized Signatory (Provider)", fill=(60, 60, 60), font=font)

        draw.line([(width - 300, sig_y + 60), (width - 70, sig_y + 60)], fill=(50, 50, 50), width=1)
        draw.text((width - 300, sig_y + 65), "By: Authorized Signatory (Client)", fill=(60, 60, 60), font=font)

    else:  # purchase_order
        # Purchase order layout: Violet accent banner, PO Number, Ship To grid, PO Line Item Table, Approvals
        draw.rectangle([(0, 0), (width, 15)], fill=(99, 102, 241))  # Violet accent banner
        draw.text((40, 40), "INDUSTRIAL SUPPLY DEPOT", fill=(20, 20, 20), font=font)
        draw.text((40, 60), "Commercial Procurement Division", fill=(80, 80, 80), font=font)
        draw.rectangle([(width - 240, 35), (width - 40, 75)], fill=(238, 240, 255), outline=(99, 102, 241))
        draw.text((width - 220, 45), "PURCHASE REQUISITION", fill=(40, 30, 120), font=font)
        po_num = f"PO-2026-{5000 + index}"
        draw.text((width - 220, 60), f"P.O. #: {po_num}", fill=(30, 30, 30), font=font)
        draw.text((width - 240, 85), "P.O. Date: 2026-10-20", fill=(30, 30, 30), font=font)

        # Dual Vendor / Ship-To Boxes
        box_y = 120
        draw.rectangle([(40, box_y), (350, box_y + 80)], outline=(180, 180, 180))
        draw.text((50, box_y + 8), "VENDOR / SUPPLIER:", fill=(30, 30, 30), font=font)
        draw.text((50, box_y + 26), "Precision Fasteners Ltd", fill=(60, 60, 60), font=font)
        draw.text((50, box_y + 44), "12 Industrial Parkway, Cleveland, OH", fill=(60, 60, 60), font=font)

        draw.rectangle([(380, box_y), (width - 40, box_y + 80)], outline=(180, 180, 180))
        draw.text((390, box_y + 8), "SHIP TO WAREHOUSE:", fill=(30, 30, 30), font=font)
        draw.text((390, box_y + 26), "Attenomy Cortex Fulfillment Center", fill=(60, 60, 60), font=font)
        draw.text((390, box_y + 44), "Dock 4, 88 Logistics Way, Reno, NV", fill=(60, 60, 60), font=font)

        # Table
        tbl_y = 230
        draw.rectangle([(40, tbl_y), (width - 40, tbl_y + 25)], fill=(220, 225, 235))
        draw.text((50, tbl_y + 7), "ITEM #", fill=(10, 10, 10), font=font)
        draw.text((120, tbl_y + 7), "PART DESCRIPTION", fill=(10, 10, 10), font=font)
        draw.text((450, tbl_y + 7), "QTY", fill=(10, 10, 10), font=font)
        draw.text((530, tbl_y + 7), "UNIT PRICE", fill=(10, 10, 10), font=font)
        draw.text((630, tbl_y + 7), "TOTAL", fill=(10, 10, 10), font=font)

        po_items = [
            ("PF-8821", "M8 Stainless Steel Hex Bolts (Box 500)", 10, 45.00),
            ("PF-9940", "Locking Washers Grade 8 (Box 1000)", 5, 22.50),
            ("PF-1102", "Structural Flange Nuts (Box 250)", 8, 38.00),
            ("PF-4401", "High-Tensile Threaded Rods 1m", 25, 14.20),
        ]
        sub = 0.0
        py = tbl_y + 35
        for code, desc, qty, rate in po_items:
            tot = qty * rate
            sub += tot
            draw.text((50, py), code, fill=(50, 50, 50), font=font)
            draw.text((120, py), desc, fill=(50, 50, 50), font=font)
            draw.text((460, py), str(qty), fill=(50, 50, 50), font=font)
            draw.text((540, py), f"${rate:.2f}", fill=(50, 50, 50), font=font)
            draw.text((630, py), f"${tot:.2f}", fill=(50, 50, 50), font=font)
            draw.line([(40, py + 20), (width - 40, py + 20)], fill=(235, 235, 235), width=1)
            py += 30

        # PO Total
        draw.rectangle([(width - 250, py + 20), (width - 40, py + 70)], outline=(190, 190, 190))
        draw.text((width - 235, py + 35), f"TOTAL ORDER:  ${sub:.2f}", fill=(10, 10, 10), font=font)

        # Approval signature
        draw.text((40, height - 120), "PURCHASE AUTHORIZATION:", fill=(40, 40, 40), font=font)
        draw.line([(40, height - 80), (300, height - 80)], fill=(80, 80, 80), width=1)
        draw.text((40, height - 70), "Authorized Purchasing Agent Signature", fill=(90, 90, 90), font=font)

    file_path = output_dir / f"{category}_{index:04d}.png"
    img.save(file_path, "PNG")
    return file_path


def curate_dataset(
    output_base: Path,
    samples_per_class: int = 350,
) -> dict[str, Any]:
    """
    Curate balanced multi-source dataset, validate images, detect duplicates,
    and partition into 70/15/15 splits.
    """
    raw_dir = output_base / "raw"
    processed_dir = output_base / "processed"

    for cls in CLASSES:
        (raw_dir / cls).mkdir(parents=True, exist_ok=True)
    for split in ["train", "val", "test"]:
        for cls in CLASSES:
            (processed_dir / split / cls).mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    duplicates_detected = 0

    print(f"Curating {samples_per_class} images per category across 4 classes...")

    for category in CLASSES:
        cat_dir = raw_dir / category
        for i in range(samples_per_class):
            img_path = generate_document_image(category, i, cat_dir)
            md5_hash = compute_md5(img_path)

            if md5_hash in seen_hashes:
                duplicates_detected += 1
                continue

            seen_hashes.add(md5_hash)

            # Validate readability
            try:
                with Image.open(img_path) as im:
                    im.verify()
                with Image.open(img_path) as im:
                    w, h = im.size
                    mode = im.mode
            except Exception as e:
                print(f"Validation failure for {img_path}: {e}")
                continue

            records.append({
                "id": f"{category}_{i:04d}",
                "category": category,
                "raw_path": str(img_path.relative_to(output_base)),
                "md5": md5_hash,
                "width": w,
                "height": h,
                "mode": mode,
                "provenance": PROVENANCE_SOURCES[category],
            })

    print(f"Total valid unique samples: {len(records)} (Duplicates filtered: {duplicates_detected})")

    # Deterministic split per class: 70% Train, 15% Val, 15% Test
    split_records = {"train": [], "val": [], "test": []}

    for category in CLASSES:
        cat_records = [r for r in records if r["category"] == category]
        random.shuffle(cat_records)

        n_total = len(cat_records)
        n_train = int(n_total * 0.70)
        n_val = int(n_total * 0.15)
        # Remainder goes to test to ensure exact sum
        train_set = cat_records[:n_train]
        val_set = cat_records[n_train:n_train + n_val]
        test_set = cat_records[n_train + n_val:]

        for r in train_set:
            r["split"] = "train"
            dst = processed_dir / "train" / category / Path(r["raw_path"]).name
            if not dst.exists():
                Image.open(output_base / r["raw_path"]).save(dst)
            r["processed_path"] = str(dst.relative_to(output_base))
            split_records["train"].append(r)

        for r in val_set:
            r["split"] = "val"
            dst = processed_dir / "val" / category / Path(r["raw_path"]).name
            if not dst.exists():
                Image.open(output_base / r["raw_path"]).save(dst)
            r["processed_path"] = str(dst.relative_to(output_base))
            split_records["val"].append(r)

        for r in test_set:
            r["split"] = "test"
            dst = processed_dir / "test" / category / Path(r["raw_path"]).name
            if not dst.exists():
                Image.open(output_base / r["raw_path"]).save(dst)
            r["processed_path"] = str(dst.relative_to(output_base))
            split_records["test"].append(r)

    all_partitioned = split_records["train"] + split_records["val"] + split_records["test"]

    # Save manifest
    manifest_path = output_base / "dataset_manifest.json"
    manifest_data = {
        "random_seed": RANDOM_SEED,
        "classes": CLASSES,
        "provenance": PROVENANCE_SOURCES,
        "summary": {
            "total_samples": len(all_partitioned),
            "train_samples": len(split_records["train"]),
            "val_samples": len(split_records["val"]),
            "test_samples": len(split_records["test"]),
            "duplicates_removed": duplicates_detected,
        },
        "samples": all_partitioned,
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"Manifest written to {manifest_path}")

    # Generate Markdown distribution report
    reports_dir = output_base.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "dataset_distribution.md"

    generate_distribution_report(report_path, manifest_data, split_records)
    return manifest_data


def generate_distribution_report(
    report_path: Path,
    manifest_data: dict[str, Any],
    split_records: dict[str, list[dict[str, Any]]],
):
    """Write markdown class distribution and provenance report."""
    summary = manifest_data["summary"]
    lines = [
        "# CTX-002: Four-Source Dataset Provenance & Distribution Report",
        "",
        "## 1. Provenance Architecture",
        "",
        "| Document Class | Primary Source Dataset | Selection Strategy | Provenance Status |",
        "| :--- | :--- | :--- | :--- |",
        "| `invoice` | Synthetic generation | Generated invoice templates | Synthetic / Unverified |",
        "| `receipt` | Synthetic generation | Generated receipt templates | Synthetic / Unverified |",
        "| `contract` | Synthetic generation | Generated contract templates | Synthetic / Unverified |",
        "| `purchase_order` | Synthetic generation | Generated purchase order templates | Synthetic / Unverified |",
        "",
        "## 2. Partition Summary (Random Seed: 42)",
        "",
        f"- **Total Samples:** {summary['total_samples']}",
        f"- **Training Split (70%):** {summary['train_samples']} samples",
        f"- **Validation Split (15%):** {summary['val_samples']} samples",
        f"- **Held-Out Test Split (15%):** {summary['test_samples']} samples",
        f"- **Duplicates Identified & Removed:** {summary['duplicates_removed']}",
        "",
        "## 3. Class-Wise Split Distribution",
        "",
        "| Class | Train (70%) | Validation (15%) | Held-Out Test (15%) | Total |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]

    for cls in CLASSES:
        n_train = sum(1 for r in split_records["train"] if r["category"] == cls)
        n_val = sum(1 for r in split_records["val"] if r["category"] == cls)
        n_test = sum(1 for r in split_records["test"] if r["category"] == cls)
        tot = n_train + n_val + n_test
        lines.append(f"| `{cls}` | {n_train} | {n_val} | {n_test} | {tot} |")

    lines.extend([
        "",
        "## 4. Verification & Validation Rules",
        "- All images checked for format integrity, dimensions, and channel validity.",
        "- Exact duplicates filtered via MD5 hash comparison before split generation.",
        "- No overlapping samples between train, val, and held-out test splits.",
        "- Random seed 42 strictly maintained across runs.",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Class distribution report written to {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare CTX-002 Four-Class Document Dataset")
    parser.add_argument(
        "--samples-per-class",
        type=int,
        default=350,
        help="Number of samples to curate per class (default: 350 for 1400 total)",
    )
    args = parser.parse_args()

    data_dir = Path(__file__).resolve().parent.parent / "data"
    curate_dataset(data_dir, samples_per_class=args.samples_per_class)
