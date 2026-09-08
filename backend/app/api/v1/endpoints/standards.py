from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db
from app.models.standard import Standard as StandardModel
from app.schemas.standard import Standard as StandardSchema
from app.schemas.search import ChatRequest, ChatResponse
from app.services.ai_engine import get_engine
from app.services.llm_service import LLMConfigurationError, LLMGenerationError
from app.services.search_svc import SearchService

router = APIRouter()

@router.get("/{standard_id}", response_model=StandardSchema)
def get_standard(standard_id: str, db: Session = Depends(get_db)):
    """
    Fetch details of a specific standard by ID.
    """
    standard = db.query(StandardModel).filter(StandardModel.id == standard_id).first()
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard


@router.get("/{standard_id}/summary")
def get_standard_summary(standard_id: str, db: Session = Depends(get_db)):
    standard = db.query(StandardModel).filter(StandardModel.id == standard_id).first()
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    if not standard.ai_summary:
        try:
            context = SearchService(db).retrieve_context(standard.title, standard_id, top_k=5)
            if not context:
                standard.ai_summary = "The available standard content does not provide enough information for a summary."
            else:
                standard.ai_summary = get_engine().summarize_standard(
                    "\n\n".join(item["text"] for item in context)
                )
        except (LLMConfigurationError, LLMGenerationError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail="Semantic retrieval is currently unavailable") from exc
        db.commit()
        db.refresh(standard)
    return {"standard_id": standard.id, "summary": standard.ai_summary}


@router.post("/{standard_id}/chat", response_model=ChatResponse)
def chat_with_standard(standard_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    standard = db.query(StandardModel).filter(StandardModel.id == standard_id).first()
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    try:
        context = SearchService(db).retrieve_context(request.new_message, standard_id, top_k=5)
        answer = get_engine().answer_from_context(
            context,
            [message.model_dump() for message in request.chat_history],
            request.new_message,
        )
    except (LLMConfigurationError, LLMGenerationError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Semantic retrieval is currently unavailable") from exc
    sources = [
        {key: item[key] for key in ("standard_id", "standard_number", "source_document", "section", "clause", "page", "chunk_id") if item.get(key) is not None}
        for item in context
    ]
    return ChatResponse(answer=answer, sources=sources)

@router.get("/", response_model=List[StandardSchema])
def list_standards(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    List all standard metadata (paginated).
    """
    standards = db.query(StandardModel).offset(skip).limit(limit).all()
    return standards
