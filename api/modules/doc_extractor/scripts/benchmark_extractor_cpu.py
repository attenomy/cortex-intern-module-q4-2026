import time

import numpy as np
from modules.doc_extractor.service import DocumentExtractor

extractor = DocumentExtractor()

invoice_text = """
INVOICE
Invoice Number: INV-2026-1001
Date: 07/11/2026
Vendor: ABC Technologies
Subtotal: 1000.00
Tax: 180.00
Total: 1180.00
"""

# Warm-up
for _ in range(5):
    extractor.extract_document(
        "benchmark",
        "invoice",
        invoice_text,
        is_image=False,
    )

# Required 100 iterations
times = []

for _ in range(100):
    start = time.perf_counter()

    extractor.extract_document(
        "benchmark",
        "invoice",
        invoice_text,
        is_image=False,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    times.append(elapsed_ms)

median = np.percentile(times, 50)
p95 = np.percentile(times, 95)

print("\nCPU BENCHMARK RESULTS")
print(f"Iterations: {len(times)}")
print(f"Median: {median:.2f} ms")
print(f"P95: {p95:.2f} ms")
print(f"Median target (<150 ms): {'PASS' if median < 150 else 'FAIL'}")
print(f"P95 target (<300 ms): {'PASS' if p95 < 300 else 'FAIL'}")
