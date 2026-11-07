# API Load Test Report

- Endpoint: `POST /api/v1/extract`
- Test type: Uvicorn HTTP load test
- Total requests: 100
- Concurrency: 20
- Warm-up requests: 5
- Successful valid responses: 100/100
- Wall time: 1.003 seconds
- Throughput: 99.66 req/s

## Client-side latency
- Median: 161.6 ms
- P95: 370.95 ms
- Max: 848.82 ms

## Service-reported latency
- Median: 0.09 ms
- P95: 0.11 ms
- Max: 0.15 ms

## HTTP status counts
```json
{
  "200": 100
}
```

## Limitations
Local Uvicorn HTTP test; excludes external network conditions. 
