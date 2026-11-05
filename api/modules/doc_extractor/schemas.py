from pydantic import BaseModel, Field
from typing import Dict, Any

class DocumentExtractionRequest(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    document_type: str = Field(..., description="Document type: invoice, receipt, contract, purchase_order")
    raw_content: str = Field(..., description="Raw text or base64 image data")

class ExtractionResponse(BaseModel):
    document_id: str
    extracted_fields: Dict[str, Any]
    schema_valid: bool
    latency_ms: float

