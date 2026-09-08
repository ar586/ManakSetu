from sqlalchemy.orm import Session
from app.services.ai_engine import get_engine
from app.db.vector_store import VectorStore
from app.models.standard import Standard
from app.schemas.search import SearchResponse, SearchResult
from app.schemas.standard import Standard as StandardSchema

class SearchService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_engine = get_engine()
        self.vector_store = VectorStore()

    def semantic_search(self, query: str, top_k: int = 5, score_threshold: float = None, standard_id: str = None) -> SearchResponse:
        # 1. Embed the natural language query
        query_embedding = self.ai_engine.embed(query)

        # 2. Search Qdrant for nearest vectors
        qdrant_results = self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            standard_id=standard_id,
        )

        if not qdrant_results:
            return SearchResponse(query=query, results=[])

        # 3. Fetch full metadata from Postgres
        standard_ids = [res.standard_id for res in qdrant_results]
        standards_query = self.db.query(Standard).filter(Standard.id.in_(standard_ids)).all()
        
        # Map IDs to Postgres standard objects for quick lookup
        standards_map = {std.id: std for std in standards_query}

        # 4. Construct final response
        results = []
        for q_res in qdrant_results:
            db_standard = standards_map.get(q_res.standard_id)
            if db_standard:
                standard_schema = StandardSchema.model_validate(db_standard)
                results.append(SearchResult(
                    standard=standard_schema,
                    similarity_score=q_res.score
                ))

        # Sort by similarity score descending
        results.sort(key=lambda x: x.similarity_score, reverse=True)

        return SearchResponse(query=query, results=results)

    def retrieve_context(self, query: str, standard_id: str, top_k: int = 5, score_threshold: float = 0.25) -> list[dict]:
        """Retrieve only Qdrant content belonging to one standard."""
        query_embedding = self.ai_engine.embed(query)
        results = self.vector_store.search(
            query_vector=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold,
            standard_id=standard_id,
        )
        return [
            {
                "text": result.payload.get("text") or result.payload.get("description") or result.title,
                "score": result.score,
                "standard_id": result.standard_id,
                "standard_number": result.standard_number,
                "source_document": result.payload.get("source_document"),
                "section": result.payload.get("section"),
                "clause": result.payload.get("clause"),
                "page": result.payload.get("page"),
                "chunk_id": result.payload.get("chunk_id"),
            }
            for result in results
        ]
