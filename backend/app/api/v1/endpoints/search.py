from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.schemas.search import SearchQuery, SearchResponse
from app.services.search_svc import SearchService

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
