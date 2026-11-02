from fastapi import APIRouter, HTTPException, Depends
from .schemas import DocumentIngestRequest, DocumentIngestResponse
from .service import AsyncDocumentIngestionService

router = APIRouter(prefix="", tags=["Document Ingestion"])
_service_instance = AsyncDocumentIngestionService()

def get_ingestion_service() -> AsyncDocumentIngestionService:
    return _service_instance

@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_document(
    request: DocumentIngestRequest,
    service: AsyncDocumentIngestionService = Depends(get_ingestion_service)
):
    try:
        return await service.ingest_document(request)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion pipeline failure: {str(exc)}")

@router.get("/ingest/health")
async def ingestion_health(service: AsyncDocumentIngestionService = Depends(get_ingestion_service)):
    return {
        "status": "healthy" if service.is_healthy else "degraded",
        "module": "doc_ingestion",
        "service": "AsyncDocumentIngestionService"
    }
