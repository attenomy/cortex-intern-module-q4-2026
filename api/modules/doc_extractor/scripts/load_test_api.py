import asyncio
import json
import math
import time
from pathlib import Path

import httpx

URL = "http://127.0.0.1:8000/api/v1/extract"
CONCURRENCY = 20
TOTAL_REQUESTS = 100
WARMUP_REQUESTS = 5
PAYLOAD = {
    "document_id": "load-test-invoice",
    "document_type": "invoice",
    "raw_content": (
        "ABC STORE\n"
        "Invoice No: INV-123\n"
        "Currency: USD\n"
        "Net Amount: USD 120.00"
    )
}
def percentile(values, p):
    ordered = sorted(values)
    index = max(0, math.ceil((p / 100) * len(ordered)) - 1)
    return round(ordered[index], 2)
async def main():
    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for _ in range(WARMUP_REQUESTS):
            response = await client.post(URL, json=PAYLOAD)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Warmup failed: {response.status_code} {response.text}"
                )
        semaphore = asyncio.Semaphore(CONCURRENCY)
        results = []
        async def send_request(index):
            payload = {**PAYLOAD, "document_id": f"load-{index:03d}"}
            async with semaphore:
                start = time.perf_counter()
                try:
                    response = await client.post(URL, json=payload)
                    elapsed = (time.perf_counter() - start) * 1000
                    body = response.json() if response.status_code == 200 else {}
                    return {
                        "status": response.status_code,
                        "client_latency_ms": round(elapsed, 2),
                        "service_latency_ms": body.get("latency_ms"),
                        "schema_valid": body.get("schema_valid", False),
                        "error": None if response.status_code == 200 else response.text,
                    }
                except Exception as exc:
                    elapsed = (time.perf_counter() - start) * 1000
                    return {
                        "status": 0,
                        "client_latency_ms": round(elapsed, 2),
                        "service_latency_ms": None,
                        "schema_valid": False,
                        "error": repr(exc),
                    }
        wall_start = time.perf_counter()
        results = await asyncio.gather(
            *(send_request(i) for i in range(TOTAL_REQUESTS))
        )
        wall_seconds = time.perf_counter() - wall_start
    client_latencies = [r["client_latency_ms"] for r in results]
    service_latencies = [
        r["service_latency_ms"]
        for r in results
        if r["service_latency_ms"] is not None
    ]
    success = sum(
        r["status"] == 200 and r["schema_valid"] for r in results
    )
    status_counts = {}
    for result in results:
        key = str(result["status"])
        status_counts[key] = status_counts.get(key, 0) + 1
    report = {
        "test_type": "Uvicorn HTTP load test",
        "endpoint": "POST /api/v1/extract",
        "total_requests": TOTAL_REQUESTS,
        "concurrency": CONCURRENCY,
        "warmup_requests": WARMUP_REQUESTS,
        "successful_valid_responses": success,
        "failed_or_invalid_responses": TOTAL_REQUESTS - success,
        "status_counts": status_counts,
        "wall_time_seconds": round(wall_seconds, 3),
        "throughput_requests_per_second": round(
            TOTAL_REQUESTS / wall_seconds, 2
        ),
        "client_latency_ms": {
            "median": percentile(client_latencies, 50),
            "p95": percentile(client_latencies, 95),
            "max": round(max(client_latencies), 2),
        },
        "service_latency_ms": {
            "median": percentile(service_latencies, 50),
            "p95": percentile(service_latencies, 95),
            "max": round(max(service_latencies), 2),
        } if service_latencies else None,
        "errors": [r["error"] for r in results if r["error"]],
        "limitations": (
            "Local Uvicorn HTTP test; excludes external network conditions. "
            ""
        ),
    }
    report_dir = Path("modules/doc_extractor/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "api_load_test.json"
    md_path = report_dir / "api_load_test.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = [
        "# API Load Test Report",
        "",
        f"- Endpoint: `{report['endpoint']}`",
        f"- Test type: {report['test_type']}",
        f"- Total requests: {TOTAL_REQUESTS}",
        f"- Concurrency: {CONCURRENCY}",
        f"- Warm-up requests: {WARMUP_REQUESTS}",
        f"- Successful valid responses: {success}/{TOTAL_REQUESTS}",
        f"- Wall time: {wall_seconds:.3f} seconds",
        f"- Throughput: {report['throughput_requests_per_second']} req/s",
        "",
        "## Client-side latency",
        f"- Median: {report['client_latency_ms']['median']} ms",
        f"- P95: {report['client_latency_ms']['p95']} ms",
        f"- Max: {report['client_latency_ms']['max']} ms",
        "",
        "## Service-reported latency",
    ]
    if report["service_latency_ms"]:
        md.extend([
            f"- Median: {report['service_latency_ms']['median']} ms",
            f"- P95: {report['service_latency_ms']['p95']} ms",
            f"- Max: {report['service_latency_ms']['max']} ms",
        ])
    else:
        md.append("- No service latency values available.")
    md.extend([
        "",
        "## HTTP status counts",
        "```json",
        json.dumps(status_counts, indent=2),
        "```",
        "",
        "## Limitations",
        report["limitations"],
    ])
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n===== API LOAD TEST RESULTS =====")
    print(json.dumps(report, indent=2))
    print("\nReports saved:")
    print(json_path)
    print(md_path)
if __name__ == "__main__":
    asyncio.run(main())
