# CTX-002 Document Extractor Runbook
## Environment
- OS: Windows
- Python: 3.12.4
- OCR Engine: Tesseract 5.5.3
- Virtual environment: Repository root .venv
## Setup
Run commands from the api directory.
1. Add Tesseract to PATH:
   E:\Program Files\Tesseract-OCR
2. Activate environment:
   ..\.venv\Scripts\Activate.ps1
3. Set Python path:
   $env:PYTHONPATH = (Get-Location).Path
4. Verify OCR:
   python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
## Test Suite
Run:
python -m pytest modules\doc_extractor\tests -q --cov=modules.doc_extractor --cov-report=term-missing
Previously verified:
- 30 tests passed
- 90% total coverage
## OCR Benchmark
Run:
python modules\doc_extractor\scripts\benchmark_ocr.py
Reports:
- reports/tuning_experiments.md
- reports/tuning_experiments.json
Best result from the 24-configuration experiment matrix:
Resolution: 512
Confidence threshold: 0.70
Denoising: none
Median: 131.93 ms
P95: 336.07 ms
This is an OCR benchmark on 30 SROIE test images, not full API extraction latency.
The older PSM 6 with DPI 300 run measured median 446.13 ms and P95 800.90 ms.
The OCR P95 target of <300 ms remains unmet.
## API Load Test
Run:
python modules\doc_extractor\scripts\load_test_api.py
Previously verified:
- 100 requests
- 20 concurrent requests
- 100 successful responses
- Throughput: 99.66 requests/second
- Client median: 161.60 ms
- Client p95: 370.95 ms
- Successful responses: 100/100
- Concurrency: 20
- Test type: Local Uvicorn HTTP with plain-text payloads.
- Sampled peak server process-tree memory: 97.55 MB.
Memory sampling includes parent and child Python processes; Tesseract was not invoked.
## Profiling
Profile data:
reports/ocr_profile.prof
Memory report:
reports/memory_profile.json
Python tracemalloc does not include Tesseract subprocess memory.
## Dataset Notes
SROIE contains real receipt data.
It does not guarantee all fields required by the strict invoice schema.
Never fabricate missing invoice numbers or currencies.
The existing 1,400-image classification dataset is synthetic and must not be represented as genuine RVL-CDIP data.
## Known Limitations
1. Classification Macro F1 is 0.6667 against a target of 0.90.
2. Purchase Order classification needs improvement.
3. OCR latency targets remain unmet.
4. The Uvicorn load test used plain-text payloads; image decoding and OCR-inclusive API latency still need a separate end-to-end load test.
5. Uvicorn HTTP load test completed; median and p95 latency targets remain unmet.
6. Sampled peak server process-tree memory was 97.55 MB during the plain-text Uvicorn load test. OCR-inclusive memory remains unmeasured.
## Operational Safety
- Preserve original documents.
- Never delete source files during extraction.
- Do not invent missing entity values.
- Treat schema validation failures explicitly.
- Record dataset provenance and benchmark configuration.
## Reproducing the SROIE Evaluation Dataset
SROIE is a local dataset dependency and is not committed to this repository.
Expected source files:
- data/sroie/processed/train.jsonl
- data/sroie/processed/test.jsonl
From the api directory, run:
python modules/doc_extractor/scripts/import_sroie.py
The importer generates:
- modules/doc_extractor/data/real_sroie/
- modules/doc_extractor/data/real_sroie/manifest.jsonl
- modules/doc_extractor/reports/sroie_import_report.md
Obtain the source dataset separately and verify its license before use.
The current SROIE evaluation covers receipts only, not all four document classes.


