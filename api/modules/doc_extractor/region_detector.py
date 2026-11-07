from collections import defaultdict
import re
from typing import Any
from modules.doc_extractor.schemas import (
    BoundingBox,
    LayoutRegion,
    RegionType,
)
TABLE_ANCHORS = {
    "QTY", "QUANTITY", "PRICE", "AMOUNT", "AMT",
    "DESC", "DESCRIPTION", "ITEM", "CODE",
    "ITEMCODE", "PRODUCT", "UNIT"
}
TOTAL_ANCHORS = {
    "TOTAL", "SUBTOTAL", "ADJUSTMENT",
    "CASH", "CHANGE", "GRAND", "TOT",
    "TOTA", "TOTAI", "ROUND"
}
def normalize_text(text: str) -> str:
    """Normalize OCR tokens by removing punctuation and OCR noise."""
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())
def _box(words: list[dict[str, Any]]) -> BoundingBox | None:
    valid = [
        w["bounding_box"]
        for w in words
        if w.get("bounding_box")
    ]
    if not valid:
        return None
    return BoundingBox(
        x_min=min(b["x_min"] for b in valid),
        y_min=min(b["y_min"] for b in valid),
        x_max=max(b["x_max"] for b in valid),
        y_max=max(b["y_max"] for b in valid),
    )
def _group_lines(words: list[dict[str, Any]]) -> list[list[dict]]:
    lines = []
    for word in sorted(
        words,
        key=lambda w: (
            (w["bounding_box"]["y_min"] +
             w["bounding_box"]["y_max"]) / 2,
            w["bounding_box"]["x_min"],
        ),
    ):
        box = word["bounding_box"]
        center = (box["y_min"] + box["y_max"]) / 2
        matching = None
        for line in lines:
            line_center = sum(
                (w["bounding_box"]["y_min"] +
                 w["bounding_box"]["y_max"]) / 2
                for w in line
            ) / len(line)
            line_height = max(
                w["bounding_box"]["y_max"] -
                w["bounding_box"]["y_min"]
                for w in line
            )
            if abs(center - line_center) <= max(8, line_height * 0.6):
                matching = line
                break
        if matching is None:
            lines.append([word])
        else:
            matching.append(word)
    return lines
def detect_layout_regions(
    words: list[dict[str, Any]],
    image_width: int,
    image_height: int,
) -> list[LayoutRegion]:
    """
    Detect candidate header, line-item table and totals regions.
    Input words must contain:
        text
        bounding_box: x_min, y_min, x_max, y_max
    These are heuristic OCR-based regions, not model predictions.
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError("Image dimensions must be positive")
    valid_words = []
    for word in words:
        box = word.get("bounding_box")
        if not box or not word.get("text", "").strip():
            continue
        x1, y1 = box["x_min"], box["y_min"]
        x2, y2 = box["x_max"], box["y_max"]
        if (
            x1 < 0 or y1 < 0 or
            x2 > image_width or y2 > image_height or
            x1 >= x2 or y1 >= y2
        ):
            continue
        valid_words.append(word)
    if not valid_words:
        return []
    lines = _group_lines(valid_words)
    table_line = None
    table_top = None
    # Combine anchors from nearby OCR lines instead of requiring
    # multiple exact anchors on one line.
    for index, line in enumerate(lines):
        nearby_lines = lines[max(0, index - 1): index + 2]
        tokens = {
            normalize_text(w["text"])
            for nearby in nearby_lines
            for w in nearby
        }
        matches = tokens & TABLE_ANCHORS
        # A single strong column anchor is sufficient for receipts
        # where OCR misses the remaining table headings.
        if matches:
            candidate = max(
                nearby_lines,
                key=lambda row: len(
                    {
                        normalize_text(w["text"])
                        for w in row
                    } & TABLE_ANCHORS
                ),
            )
            candidate_matches = {
                normalize_text(w["text"])
                for w in candidate
            } & TABLE_ANCHORS
            if candidate_matches:
                table_line = candidate
                table_top = min(
                    w["bounding_box"]["y_min"]
                    for w in table_line
                )
                break
    # Fallback: infer a table start from repeated item-like rows
    # when OCR misses all column headings.
    if table_top is None:
        candidate_rows = []
        for line in lines:
            if len(line) < 2:
                continue
            numeric_count = sum(
                bool(re.search(r"\d", str(w["text"])))
                for w in line
            )
            if numeric_count >= 1 and len(line) >= 2:
                candidate_rows.append(line)
        for index in range(len(candidate_rows) - 1):
            first = candidate_rows[index]
            second = candidate_rows[index + 1]
            first_y = min(w["bounding_box"]["y_min"] for w in first)
            second_y = min(w["bounding_box"]["y_min"] for w in second)
            if 0 < second_y - first_y < image_height * 0.12:
                table_line = first
                table_top = first_y
                break
    total_words = [
        w for w in valid_words
        if normalize_text(w["text"]) in TOTAL_ANCHORS
    ]
    regions = []
    # Header: content above the detected table header.
    if table_top is not None:
        header_words = [
            w for w in valid_words
            if w["bounding_box"]["y_max"] <= table_top
        ]
        header_box = _box(header_words)
        if header_box:
            regions.append(
                LayoutRegion(
                    region_type=RegionType.HEADER,
                    bounding_box=header_box,
                )
            )
    # Table: from column headers until the first totals anchor.
    if table_top is not None:
        later_totals = [
            w for w in total_words
            if w["bounding_box"]["y_min"] > table_top
        ]
        table_bottom = (
            min(w["bounding_box"]["y_min"] for w in later_totals)
            if later_totals
            else int(image_height * 0.85)
        )
        table_words = [
            w for w in valid_words
            if (
                w["bounding_box"]["y_max"] >= table_top
                and w["bounding_box"]["y_min"] < table_bottom
            )
        ]
        table_box = _box(table_words)
        if table_box:
            regions.append(
                LayoutRegion(
                    region_type=RegionType.LINE_ITEM_TABLE,
                    bounding_box=table_box,
                )
            )
    # Totals: from first total anchor to last payment-related anchor.
    if total_words:
        totals_top = min(
            w["bounding_box"]["y_min"] for w in total_words
        )
        totals_bottom = max(
            w["bounding_box"]["y_max"] for w in total_words
        )
        totals_words = [
            w for w in valid_words
            if (
                w["bounding_box"]["y_min"] >= totals_top
                and w["bounding_box"]["y_max"] <= totals_bottom
            )
        ]
        totals_box = _box(totals_words)
        if totals_box:
            regions.append(
                LayoutRegion(
                    region_type=RegionType.TOTALS_BLOCK,
                    bounding_box=totals_box,
                )
            )
    return regions
