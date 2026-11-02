import time
import uuid
import hashlib
import re
from typing import Dict, Any, List, Tuple
from .schemas import DocumentIngestRequest, DocumentIngestResponse, DocumentChunk, IngestionSourceType

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are\s+now", re.IGNORECASE),
    re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"drop\s+table\s+", re.IGNORECASE)
]

class AsyncDocumentIngestionService:
    """Enterprise multi-source document ingestion, sanitization, and chunking service."""

    def __init__(self):
        self.is_healthy = True

    def sanitize_payload(self, text: str) -> Tuple[str, List[str]]:
        sanitization_flags = []
        cleaned_text = text

        for pattern in PROMPT_INJECTION_PATTERNS:
            if pattern.search(cleaned_text):
                sanitization_flags.append(f"FLAGGED_PATTERN: {pattern.pattern}")
                cleaned_text = pattern.sub("[REDACTED_SECURITY_ALERT]", cleaned_text)

        # Strip null bytes and non-printable control characters
        cleaned_text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned_text)

        return cleaned_text, sanitization_flags

    def chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []
        step = chunk_size - chunk_overlap
        if step <= 0:
            step = chunk_size

        text_len = len(text)
        start_idx = 0
        chunk_counter = 0

        while start_idx < text_len:
            end_idx = min(start_idx + chunk_size, text_len)
            segment = text[start_idx:end_idx]

            chunk_hash = hashlib.sha256(segment.encode("utf-8")).hexdigest()
            # Approximate token count (1 token roughly equals 4 chars)
            est_tokens = max(1, len(segment) // 4)

            chunks.append(DocumentChunk(
                chunk_id=str(uuid.uuid4())[:8],
                chunk_index=chunk_counter,
                text=segment,
                token_count=est_tokens,
                hash_sha256=chunk_hash
            ))

            chunk_counter += 1
            if end_idx >= text_len:
                break
            start_idx += step

        return chunks

    async def ingest_document(self, request: DocumentIngestRequest) -> DocumentIngestResponse:
        t0 = time.perf_counter()

        cleaned_text, flags = self.sanitize_payload(request.raw_payload)
        chunks = self.chunk_text(cleaned_text, request.chunk_size, request.chunk_overlap)
        total_tokens = sum(c.token_count for c in chunks)

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"

        return DocumentIngestResponse(
            document_id=doc_id,
            status="ingested" if not flags else "sanitized",
            source_type=request.source_type,
            total_chunks=len(chunks),
            total_tokens=total_tokens,
            sanitization_flags=flags,
            chunks=chunks,
            latency_ms=elapsed_ms
        )
