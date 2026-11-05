# Module: Intent Router (`api/modules/intent_router/`)

> **Assigned Engineer**: Abhishek Adbhute (`@abhishekadbhute-create`)  
> **Ticket**: `[CTX-001]` Neural Intent Router & Sub-50ms CPU Inference Engine  
> **Target Branch**: `feature/CTX-001-intent-router` -> `staging`  

---

## Module Overview
The Intent Router classifies incoming natural language queries across specialized agent sub-graphs:
- `finance`: invoice and billing extraction
- `support`: engineering and customer triage
- `search`: enterprise RAG knowledge engine
- `orchestration`: multi-agent workflow execution

## Key Constraints
- **Latency Budget**: Must execute with p95 `< 50ms` on CPU.
- **Model**: Pre-trained `DistilBERT` or `all-MiniLM-L6-v2` fine-tuned and exported to ONNX runtime.
- **Confidence**: Must provide confidence score and deterministic fallback when confidence is `< 0.60`.

## Testing
Run unit tests for this module:
```bash
pytest modules/intent_router/tests/ -v
```

