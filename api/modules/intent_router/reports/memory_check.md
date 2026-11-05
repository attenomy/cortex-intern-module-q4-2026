# Memory check (5000 requests)
Hardware: `{"python": "3.12.10", "os": "Windows-11-10.0.26300-SP0", "cpu": "Intel64 Family 6 Model 186 Stepping 2, GenuineIntel", "logical_cpus": 12, "ram_gb": 16.8, "onnxruntime": "1.31.1"}`
| after requests | Python KB (tracemalloc) | RSS MB |
|---|---|---|
| 1000 | 20.7 | 189.9 |
| 2000 | 29.0 | 189.9 |
| 3000 | 36.0 | 190.1 |
| 4000 | 40.7 | 190.1 |
| 5000 | 56.8 | 190.2 |

Growth block 1 -> block 5: Python +36.1 KB (limit 512), RSS +0.3 MB (limit 10)
RSS right after model load: 187 MB; after the run: 190 MB (ticket limit 250 MB for this process; the full API process is measured in load_test)

**Verdict: PASS**

Top allocation differences (block 5 vs block 1):

```
D:\intern_project\cortex-intern-module-q4-2026\.venv\Lib\site-packages\onnxruntime\capi\onnxruntime_inference_collection.py:395: size=52.4 KiB (+32.3 KiB), count=759 (+475), average=71 B
C:\Users\Abhishek Adbhute\AppData\Local\Programs\Python\Python312\Lib\tracemalloc.py:560: size=1200 B (+1200 B), count=8 (+8), average=150 B
C:\Users\Abhishek Adbhute\AppData\Local\Programs\Python\Python312\Lib\tracemalloc.py:423: size=1200 B (+1200 B), count=8 (+8), average=150 B
D:\intern_project\cortex-intern-module-q4-2026\api\modules\intent_router\profiling\memory_check.py:44: size=984 B (+768 B), count=11 (+8), average=89 B
C:\Users\Abhishek Adbhute\AppData\Local\Programs\Python\Python312\Lib\tracemalloc.py:558: size=504 B (+448 B), count=9 (+8), average=56 B
```
