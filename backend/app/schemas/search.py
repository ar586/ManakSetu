from pydantic import BaseModel, Field
from typing import Any, List, Optional
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


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    chat_history: List[ChatMessage] = Field(default_factory=list)
    new_message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict] = Field(default_factory=list)


class ComplianceAnalysis(BaseModel):
    summary: str
    conflicts: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    compliance_gaps: List[str] = Field(default_factory=list)
    clauses_to_watch: List[str] = Field(default_factory=list)


class TenderFinding(BaseModel):
    tender_requirement: Optional[str] = None
    matched_standard: Optional[str] = None
    standard_id: Optional[str] = None
    standard_number: Optional[str] = None
    relevance_score: Optional[float] = None
    source_document: Optional[str] = None
    clause: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    compliance_status: str = "insufficient_evidence"
    explanation: str


class DocumentStandardMatch(BaseModel):
    standard: Standard
    similarity_score: float
    sources: List[dict] = Field(default_factory=list)


class DocumentAnalysisResponse(BaseModel):
    filename: str
    extracted_text_preview: str
    matched_standards: List[DocumentStandardMatch]
    findings: List[TenderFinding] = Field(default_factory=list)
    compliance_analysis: ComplianceAnalysis
