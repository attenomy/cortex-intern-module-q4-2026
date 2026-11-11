def calculate_iou(box_a, box_b):
    def get(box, key):
        return box[key] if isinstance(box, dict) else getattr(box, key)
    ax1, ay1 = get(box_a, "x_min"), get(box_a, "y_min")
    ax2, ay2 = get(box_a, "x_max"), get(box_a, "y_max")
    bx1, by1 = get(box_b, "x_min"), get(box_b, "y_min")
    bx2, by2 = get(box_b, "x_max"), get(box_b, "y_max")
    if ax1 >= ax2 or ay1 >= ay2:
        raise ValueError("Invalid first bounding box")
    if bx1 >= bx2 or by1 >= by2:
        raise ValueError("Invalid second bounding box")
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0
def evaluate_regions(predicted, ground_truth):
    results = {}
    for gt in ground_truth:
        name = gt.region_type.value
        pred = next(
            (p for p in predicted if p.region_type == gt.region_type),
            None,
        )
        results[name] = (
            calculate_iou(pred.bounding_box, gt.bounding_box)
            if pred else 0.0
        )
    scores = list(results.values())
    return {
        "regions": results,
        "mean_iou": sum(scores) / len(scores) if scores else 0.0,
        "target_met": bool(scores) and all(x >= 0.75 for x in scores),
    }
