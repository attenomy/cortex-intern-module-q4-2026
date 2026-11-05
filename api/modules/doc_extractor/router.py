from fastapi import APIRouter, HTTPException
from .schemas import DocumentExtractionRequest, ExtractionResponse
from .service import DocumentExtractor

router = APIRouter(prefix="/extract", tags=["Document Extraction"])
service = DocumentExtractor()

@router.post("", response_model=ExtractionResponse)
def extract_document_endpoint(req: DocumentExtractionRequest):
    if not req.document_id.strip():
        raise HTTPException(status_code=400, detail="document_id cannot be empty")
    return service.extract_document(req.document_id, req.document_type, req.raw_content)

