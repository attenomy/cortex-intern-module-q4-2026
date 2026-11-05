import re
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator

class IngestionSourceType(str, Enum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    WEB_STREAM = "web_stream"

class IngestionPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class DocumentChunk(BaseModel):
    chunk_id: str
    chunk_index: int
    text: str
    token_count: int
    hash_sha256: str

class DocumentIngestRequest(BaseModel):
    source_type: IngestionSourceType = Field(default=IngestionSourceType.PLAIN_TEXT, description="Source format of the document")
    raw_payload: str = Field(..., description="Raw text content or base64 encoded document stream")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags including author, source url, and tags")
    priority: IngestionPriority = Field(default=IngestionPriority.NORMAL, description="Processing queue priority")
    chunk_size: int = Field(default=512, ge=64, le=4096, description="Target chunk token/character size")
    chunk_overlap: int = Field(default=64, ge=0, le=512, description="Target sliding overlap window")

    @validator("raw_payload")
    def validate_payload_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Document payload cannot be empty or whitespace only")
        return v

    @validator("chunk_overlap")
    def validate_overlap_less_than_size(cls, v: int, values: Dict[str, Any]) -> int:
        if "chunk_size" in values and v >= values["chunk_size"]:
            raise ValueError("chunk_overlap must be strictly less than chunk_size")
        return v

class DocumentIngestResponse(BaseModel):
    document_id: str
    status: str
    source_type: IngestionSourceType
    total_chunks: int
    total_tokens: int
    sanitization_flags: List[str]
    chunks: List[DocumentChunk]
    latency_ms: float

