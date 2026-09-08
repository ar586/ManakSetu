from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.schemas.search import SearchQuery, SearchResponse
from app.services.search_svc import SearchService
from app.schemas.search import DocumentAnalysisResponse
from app.services.document_svc import analyze_document
from app.services.llm_service import LLMConfigurationError, LLMGenerationError

router = APIRouter()

@router.post("/", response_model=SearchResponse)
def search_standards(query_data: SearchQuery, db: Session = Depends(get_db)):
    """
    Search for Indian Standards using semantic similarity (AI).
    Provide a tender description or product specifications.
    """
    search_svc = SearchService(db)
    results = search_svc.semantic_search(
        query=query_data.query,
        top_k=query_data.top_k,
        score_threshold=query_data.score_threshold
    )
    return results


@router.post("/document", response_model=DocumentAnalysisResponse)
async def analyze_uploaded_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        return await analyze_document(file, db)
    except (LLMConfigurationError, LLMGenerationError) as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Semantic retrieval is currently unavailable") from exc
