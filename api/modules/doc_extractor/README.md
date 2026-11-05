# Module: Document Extractor (`api/modules/doc_extractor/`)

> **Assigned Engineer**: Abhinav Singh (`@Abhinav55849`)  
> **Ticket**: `[CTX-002]` Cognitive Document Entity Extractor & Layout Classifier  
> **Target Branch**: `feature/CTX-002-doc-extractor` -> `staging`  

---

## Module Overview
The Document Extractor provides multimodal layout classification and structured entity parsing for enterprise invoices, receipts, legal contracts, and purchase orders.

## Key Constraints
- **Model**: Fine-tuned `MobileNetV3` or OpenCV document layout feature pipeline.
- **Validation**: Schema validation confirming extracted entities conform to structured invoice schema (`vendor_name`, `invoice_number`, `net_amount`, `currency`).
- **Resilience**: Invalid or corrupted base64 images must return structured HTTP 422 JSON errors rather than 500 server crashes.

## Testing
Run unit tests for this module:
```bash
pytest modules/doc_extractor/tests/ -v
```

