from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.standard import Standard

class SearchQuery(BaseModel):
    query: str = Field(..., description="The tender description or natural language query")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)
    score_threshold: Optional[float] = Field(None, description="Minimum similarity score")

class SearchResult(BaseModel):
    standard: Standard
    similarity_score: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
