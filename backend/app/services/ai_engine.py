"""
AI Engine for semantic embedding generation.

Provides multilingual embedding capabilities using sentence-transformers.
Handles model loading, caching, and batch processing for efficiency.
"""

import logging
import os
import json
from typing import List, Optional
import numpy as np
from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

# sentence-transformers is imported at module level (rather than lazily inside
# `_load_model()`) so it can be patched/mocked in tests via
# `app.services.ai_engine.SentenceTransformer`, and so import failures surface
# consistently through `_load_model()`.
try:
    from sentence_transformers import SentenceTransformer
    _SENTENCE_TRANSFORMERS_IMPORT_ERROR: Optional[str] = None
except ImportError as _import_exc:  # pragma: no cover - exercised only if dependency missing
    SentenceTransformer = None  # type: ignore
    _SENTENCE_TRANSFORMERS_IMPORT_ERROR = str(_import_exc)

# Global model cache - loaded once on first use
_model_cache = None
_model_name_cache = None

# Default number of texts sent to the embedding model's encode() call at once.
# This is distinct from QDRANT_BATCH_SIZE (used by the ingestion script when
# upserting points to Qdrant) - the two batch sizes control different stages
# of the pipeline and must not be confused.
DEFAULT_EMBEDDING_BATCH_SIZE = 32


def get_embedding_model_name() -> str:
    """
    Get the embedding model name from environment or use default.

    Returns:
        Model name/path for sentence-transformers
    """
    return os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )


def get_embedding_batch_size() -> int:
    """
    Get the embedding model batch size from environment or use default.

    This controls how many texts are sent to the embedding model's encode()
    call at once. It is NOT the same as QDRANT_BATCH_SIZE, which controls how
    many points are upserted to Qdrant at once (see scripts/ingest_standards.py).

    Returns:
        Batch size for sentence-transformers encode() calls
    """
    raw_value = os.getenv("EMBEDDING_BATCH_SIZE", str(DEFAULT_EMBEDDING_BATCH_SIZE))
    try:
        batch_size = int(raw_value)
    except ValueError:
        logger.warning(
            f"Invalid EMBEDDING_BATCH_SIZE={raw_value!r}, "
            f"falling back to default {DEFAULT_EMBEDDING_BATCH_SIZE}"
        )
        return DEFAULT_EMBEDDING_BATCH_SIZE

    if batch_size <= 0:
        logger.warning(
            f"EMBEDDING_BATCH_SIZE must be positive, got {batch_size}. "
            f"Falling back to default {DEFAULT_EMBEDDING_BATCH_SIZE}"
        )
        return DEFAULT_EMBEDDING_BATCH_SIZE

    return batch_size


def _load_model():
    """
    Load the embedding model (called once, result cached).

    Returns:
        Loaded sentence-transformer model

    Raises:
        ImportError: If sentence-transformers not installed
        RuntimeError: If model loading fails
    """
    global _model_cache, _model_name_cache

    if _model_cache is not None:
        return _model_cache

    if SentenceTransformer is None:
        raise ImportError(
            "sentence-transformers not installed. "
            f"Install with: pip install sentence-transformers ({_SENTENCE_TRANSFORMERS_IMPORT_ERROR})"
        )

    model_name = get_embedding_model_name()

    try:
        logger.info(f"Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name)
        _model_cache = model
        _model_name_cache = model_name
        logger.info(f"Model loaded successfully. Dimension: {model.get_sentence_embedding_dimension()}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise RuntimeError(f"Failed to load embedding model: {e}")


class AIEngine:
    """
    Embedding service for semantic text representation.

    Provides single and batch embedding using multilingual sentence transformers.
    Model is loaded once and reused for efficiency.
    """

    def __init__(self):
        """Initialize AI Engine (model loaded on first use)."""
        self._model = None

    @property
    def model(self):
        """Lazy load model on first access."""
        if self._model is None:
            self._model = _load_model()
        return self._model

    @property
    def dimension(self) -> int:
        """
        Get embedding dimension from loaded model.

        Returns:
            Vector dimension for embeddings
        """
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed (can be empty after calling validate)

        Returns:
            Embedding as list of floats

        Raises:
            ValueError: If text is empty or whitespace-only
            RuntimeError: If embedding fails
        """
        # Validate input
        is_valid, error_msg = self._validate_input(text)
        if not is_valid:
            raise ValueError(error_msg)

        try:
            # SentenceTransformer returns numpy array
            embedding = self.model.encode(
                text,
                convert_to_tensor=False,
                normalize_embeddings=True  # L2 normalization
            )
            # Convert to Python list
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Embedding failed for text: {text[:100]}... Error: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")

    def embed_batch(
        self,
        texts: List[str],
        show_progress_bar: bool = False,
        batch_size: Optional[int] = None,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Batch processing is much faster than individual embeddings.

        The entire input list is validated up front. If any text is invalid
        (empty, whitespace-only, or not a string), a ValueError is raised for
        the whole batch rather than silently dropping that entry - dropping
        entries would misalign the returned embeddings with the caller's
        original list of texts/records. The caller's list is never mutated.

        Args:
            texts: List of texts to embed
            show_progress_bar: Show progress bar during embedding
            batch_size: Number of texts to send to the model's encode() call
                at once (from EMBEDDING_BATCH_SIZE env var if None). This is
                distinct from QDRANT_BATCH_SIZE, which controls Qdrant upsert
                batching.

        Returns:
            List of embeddings (each as list of floats), in the same order
            as `texts` - one embedding per input text.

        Raises:
            ValueError: If texts is not a list, is empty, or contains any
                invalid (empty/whitespace/non-string) entry.
            RuntimeError: If batch embedding fails
        """
        if not isinstance(texts, list):
            raise ValueError(f"Expected list of texts, got {type(texts)}")

        if not texts:
            raise ValueError("Cannot embed empty list")

        # Validate the entire batch up front without mutating the caller's list.
        invalid_entries = []
        for i, text in enumerate(texts):
            is_valid, error_msg = self._validate_input(text)
            if not is_valid:
                invalid_entries.append(f"index {i}: {error_msg}")

        if invalid_entries:
            raise ValueError(
                f"Batch contains {len(invalid_entries)} invalid text(s): "
                f"{'; '.join(invalid_entries)}"
            )

        effective_batch_size = batch_size if batch_size is not None else get_embedding_batch_size()

        try:
            logger.info(
                f"Embedding batch of {len(texts)} texts "
                f"(encode batch_size={effective_batch_size})"
            )

            # SentenceTransformer batch encoding
            embeddings = self.model.encode(
                texts,
                batch_size=effective_batch_size,
                convert_to_tensor=False,
                normalize_embeddings=True,  # L2 normalization
                show_progress_bar=show_progress_bar
            )

            # Convert numpy array to list of lists
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise RuntimeError(f"Batch embedding generation failed: {e}")

    @staticmethod
    def _validate_input(text: str) -> tuple[bool, Optional[str]]:
        """
        Validate text for embedding.

        Args:
            text: Text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text:
            return False, "Text cannot be empty"

        if not isinstance(text, str):
            return False, f"Text must be string, got {type(text).__name__}"

        if not text.strip():
            return False, "Text cannot be whitespace-only"

        return True, None

    def similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Embeddings should be normalized (L2 norm = 1).

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0 to 1 for normalized vectors)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Cosine similarity for normalized vectors is just dot product
            similarity = np.dot(vec1, vec2)

            # Clamp to [0, 1] due to floating point precision
            similarity = float(max(0.0, min(1.0, similarity)))

            return similarity
        except Exception as e:
            logger.error(f"Similarity calculation failed: {e}")
            raise RuntimeError(f"Failed to calculate similarity: {e}")

    def generate(self, system_prompt: str, user_prompt: str, fallback: str = "") -> str:
        """Delegate generation to the backend-only LLM provider service."""
        return get_llm_service().generate(system_prompt, user_prompt)

    def summarize_standard(self, standard_text: str) -> str:
        return self.generate(
            "You summarize Indian Standards for civil engineers. Be precise and concise.",
            "Summarize the following Indian Standard in 3-4 bullet points for a civil engineer.\n\n"
            + standard_text[:24000],
        )

    def answer_from_context(self, context: list[dict], history: list, question: str, standard_metadata: str = "") -> str:
        """Answer using retrieved Qdrant chunks and general knowledge."""
        context_text = ""
        if context:
            context_text = "\n\n".join(
                "SOURCE " + str(index + 1) + ": " + item["text"]
                + "\nMETADATA: " + ", ".join(
                    f"{key}={item[key]}" for key in ("standard_id", "standard_number", "source_document", "section", "clause", "page", "chunk_id")
                    if item.get(key) is not None
                )
                for index, item in enumerate(context)
            )
        else:
            context_text = "No direct text chunks retrieved."
            
        history_text = "\n".join(
            f"{message.get('role', 'user')}: {message.get('content', '')}" for message in history[-8:]
        )
        return self.generate(
            "You are an expert on Indian Standards and civil engineering. "
            "Use the provided context to answer the user's question if possible. "
            "If the provided context is insufficient, you are allowed to use your pre-trained knowledge to provide a helpful, accurate answer. "
            "When using your general knowledge, be helpful but advise the user to consult the official standard document for exact clauses.",
            f"RETRIEVED STANDARD CONTENT:\n{context_text}\n\nCHAT HISTORY:\n{history_text}\n\nQUESTION:\n{question}",
        )
    def analyze_compliance(self, tender_text: str, matched_standards: list[dict]) -> dict:
        prompt = (
            "Compare the requirements in the tender document against the matched Indian Standards. "
            "Return ONLY valid JSON with keys summary, findings, conflicts, gaps, recommendations. "
            "Each finding must contain tender_requirement, matched_standard, relevance_score, clause, section, page, "
            "compliance_status, and explanation. compliance_status must be exactly one of compliant, non_compliant, "
            "partially_compliant, or insufficient_evidence. Never infer compliance from similarity alone and never "
            "invent source metadata.\n\n"
            f"TENDER:\n{tender_text[:24000]}\n\nMATCHED STANDARDS:\n{json.dumps(matched_standards)[:18000]}"
        )
        result = get_llm_service().generate_json(
            "You are a compliance analyst for Indian civil engineering tenders.",
            prompt,
        )
        result.setdefault("summary", "The available evidence was insufficient for a definitive compliance conclusion.")
        result.setdefault("findings", [])
        result.setdefault("conflicts", [])
        result.setdefault("gaps", [])
        result.setdefault("recommendations", [])
        return result


# Module-level convenience functions
_engine_instance = None


def get_engine() -> AIEngine:
    """
    Get or create singleton AI Engine instance.

    Returns:
        AIEngine instance
    """
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AIEngine()
    return _engine_instance


def embed(text: str) -> List[float]:
    """Convenience function for single text embedding."""
    return get_engine().embed(text)


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Convenience function for batch embedding."""
    return get_engine().embed_batch(texts)


def get_dimension() -> int:
    """Convenience function to get embedding dimension."""
    return get_engine().dimension


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    engine = AIEngine()

    # Test single embedding
    text = "LED street lighting for outdoor road applications"
    print(f"Embedding: {text}")
    embedding = engine.embed(text)
    print(f"Dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

    # Test batch embedding
    texts = [
        "LED street lighting",
        "Safety requirements for electrical equipment",
        "Concrete specifications for construction"
    ]

    print(f"\nBatch embedding {len(texts)} texts...")
    embeddings = engine.embed_batch(texts)
    print(f"Generated {len(embeddings)} embeddings")

    # Test similarity
    sim = engine.similarity(embeddings[0], embeddings[1])
    print(f"Similarity between first two: {sim:.4f}")
