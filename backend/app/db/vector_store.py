"""
Vector store implementation using Qdrant for semantic search.

Manages vector storage, indexing, and similarity search operations.
Automatically creates collections and handles vector persistence.
"""

import logging
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# qdrant-client is imported at module level (rather than lazily inside methods)
# so that:
#   1. It can be patched/mocked in tests via `app.db.vector_store.QdrantClient`.
#   2. Failures to import surface consistently through `_create_client()`.
try:
    from qdrant_client import QdrantClient, models
    from qdrant_client.models import Distance, VectorParams, PointStruct, PointIdsList
    _QDRANT_IMPORT_ERROR: Optional[str] = None
except ImportError as _import_exc:  # pragma: no cover - exercised only if dependency missing
    QdrantClient = None  # type: ignore
    models = None  # type: ignore
    Distance = None  # type: ignore
    VectorParams = None  # type: ignore
    PointStruct = None  # type: ignore
    PointIdsList = None  # type: ignore
    _QDRANT_IMPORT_ERROR = str(_import_exc)


@dataclass
class SearchResult:
    """Single search result from vector store."""
    point_id: int
    score: float
    standard_id: str
    standard_number: str
    title: str
    payload: Dict[str, Any]


def get_qdrant_url() -> str:
    """Get Qdrant server URL from environment."""
    return os.getenv("QDRANT_URL", "http://localhost:6333")


def get_qdrant_api_key() -> Optional[str]:
    """Get Qdrant API key from environment, if configured (e.g. Qdrant Cloud)."""
    return os.getenv("QDRANT_API_KEY") or None


def get_qdrant_collection() -> str:
    """Get Qdrant collection name from environment."""
    return os.getenv("QDRANT_COLLECTION", "indian_standards")


def get_vector_score_threshold() -> float:
    """Get similarity score threshold from environment."""
    return float(os.getenv("VECTOR_SCORE_THRESHOLD", "0.0"))


class VectorStore:
    """
    Qdrant-based vector store for semantic search.

    Manages collection creation, vector upsert, and similarity search.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        collection_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize Vector Store.

        Args:
            url: Qdrant server URL (from env if None)
            collection_name: Collection name (from env if None)
            api_key: Qdrant API key, e.g. for Qdrant Cloud (from env if None)
        """
        self.url = url or get_qdrant_url()
        self.collection_name = collection_name or get_qdrant_collection()
        self.api_key = api_key or get_qdrant_api_key()
        self._client = None

    @property
    def client(self):
        """Lazy load and cache Qdrant client."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        """
        Create Qdrant client.

        Returns:
            Initialized Qdrant client

        Raises:
            ImportError: If qdrant-client not installed
            RuntimeError: If connection fails
        """
        if QdrantClient is None:
            raise ImportError(
                "qdrant-client not installed. "
                f"Install with: pip install qdrant-client ({_QDRANT_IMPORT_ERROR})"
            )

        try:
            logger.info(f"Connecting to Qdrant at {self.url}")
            client = QdrantClient(url=self.url, api_key=self.api_key)

            # Test connection
            client.get_collections()
            logger.info("Connected to Qdrant successfully")

            return client
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant at {self.url}: {e}")
            raise RuntimeError(f"Failed to connect to Qdrant: {e}")

    def ensure_collection(self, vector_size: int, recreate: bool = False) -> None:
        """
        Ensure collection exists with correct vector size.

        Creates collection if it doesn't exist.
        Validates vector size if it does exist.

        Args:
            vector_size: Expected embedding dimension
            recreate: If True, recreate collection (deletes data)

        Raises:
            RuntimeError: If collection validation fails
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name in collection_names:
                if recreate:
                    logger.info(f"Recreating collection: {self.collection_name}")
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(f"Collection exists: {self.collection_name}")
                    # Validate vector size
                    collection_info = self.client.get_collection(self.collection_name)
                    existing_size = collection_info.config.params.vectors.size

                    if existing_size != vector_size:
                        raise RuntimeError(
                            f"Vector size mismatch. Expected {vector_size}, "
                            f"got {existing_size}. Drop collection to recreate."
                        )
                    return

            # Create collection
            logger.info(f"Creating collection: {self.collection_name} (dim={vector_size})")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE  # Good for normalized embeddings
                )
            )

            logger.info(f"Collection created successfully")

        except Exception as e:
            logger.error(f"Failed to ensure collection: {e}")
            raise RuntimeError(f"Collection setup failed: {e}")

    def upsert(
        self,
        points: List[Dict[str, Any]],
        vector_key: str = "vector"
    ) -> int:
        """
        Upsert vectors into collection.

        Each point should have format:
        {
            "id": unique_int_id,
            "vector": list_of_floats,
            "payload": {
                "standard_id": "TEST-001",
                "standard_number": "TEST-STANDARD-001",
                "title": "...",
                "text": "...",
                ...
            }
        }

        Args:
            points: List of points to upsert
            vector_key: Key containing vector in each point (default "vector")

        Returns:
            Number of points upserted

        Raises:
            ValueError: If points format is invalid
            RuntimeError: If upsert fails
        """
        if not points:
            logger.warning("No points to upsert")
            return 0

        if not isinstance(points, list):
            raise ValueError(f"Expected list of points, got {type(points)}")

        # Validate and convert to PointStruct format first, outside the
        # Qdrant-call try/except below, so malformed input raises ValueError
        # (as documented) instead of being caught and rewrapped as a generic
        # RuntimeError.
        qdrant_points = []
        for i, point in enumerate(points):
            if not isinstance(point, dict):
                raise ValueError(f"Point {i} must be dict, got {type(point)}")

            if "id" not in point or vector_key not in point or "payload" not in point:
                raise ValueError(
                    f"Point {i} missing required keys: id, {vector_key}, payload"
                )

            qdrant_points.append(
                PointStruct(
                    id=point["id"],
                    vector=point[vector_key],
                    payload=point["payload"]
                )
            )

        try:
            # Upsert in batch
            logger.info(f"Upserting {len(qdrant_points)} points...")
            self.client.upsert(
                collection_name=self.collection_name,
                points=qdrant_points
            )

            logger.info(f"Successfully upserted {len(qdrant_points)} points")
            return len(qdrant_points)

        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            raise RuntimeError(f"Failed to upsert points: {e}")

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        standard_id: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score (from env if None)

        Returns:
            List of SearchResult objects

        Raises:
            ValueError: If query_vector is invalid
            RuntimeError: If search fails
        """
        if not query_vector:
            raise ValueError("query_vector cannot be empty")

        if not isinstance(query_vector, (list, tuple)):
            raise ValueError(f"Expected list/tuple vector, got {type(query_vector)}")

        if top_k <= 0:
            raise ValueError("top_k must be positive")

        threshold = score_threshold if score_threshold is not None else get_vector_score_threshold()

        try:
            # Perform search using the current Qdrant query API.
            # `client.search(...)` was removed from recent Qdrant server/client
            # versions in favor of `client.query_points(...)`.
            query_kwargs = {
                "collection_name": self.collection_name,
                "query": query_vector,
                "limit": top_k,
                "score_threshold": threshold if threshold > 0 else None,
                "with_payload": True,
            }
            if standard_id and models is not None:
                query_kwargs["query_filter"] = models.Filter(
                    must=[models.FieldCondition(key="standard_id", match=models.MatchValue(value=standard_id))]
                )

            query_response = self.client.query_points(
                **query_kwargs,
            )

            # Convert results
            results = []
            for scored_point in query_response.points:
                payload = scored_point.payload or {}

                result = SearchResult(
                    point_id=scored_point.id,
                    score=scored_point.score,
                    standard_id=payload.get("standard_id", ""),
                    standard_number=payload.get("standard_number", ""),
                    title=payload.get("title", ""),
                    payload=payload
                )
                results.append(result)

            logger.info(f"Search returned {len(results)} results (threshold: {threshold})")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Vector search failed: {e}")

    def delete(self, point_ids: List[int]) -> int:
        """
        Delete points from collection.

        Args:
            point_ids: List of point IDs to delete

        Returns:
            Number of points deleted

        Raises:
            RuntimeError: If deletion fails
        """
        if not point_ids:
            logger.warning("No points to delete")
            return 0

        try:
            logger.info(f"Deleting {len(point_ids)} points...")

            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=point_ids)
            )

            logger.info(f"Deleted {len(point_ids)} points")
            return len(point_ids)

        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            raise RuntimeError(f"Failed to delete points: {e}")

    def health_check(self) -> bool:
        """
        Check if Qdrant is healthy and collection exists.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get collection info
            self.client.get_collection(self.collection_name)
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get collection metadata.

        Returns:
            Dictionary with collection info
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)

            return {
                "name": self.collection_name,
                "points_count": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": str(collection_info.config.params.vectors.distance),
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}

    def clear_collection(self) -> None:
        """Delete and recreate collection (clears all data)."""
        try:
            logger.warning(f"Clearing collection: {self.collection_name}")
            self.client.delete_collection(self.collection_name)
            logger.info("Collection cleared")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise RuntimeError(f"Failed to clear collection: {e}")


if __name__ == "__main__":
    # Example usage (requires running Qdrant)
    logging.basicConfig(level=logging.INFO)

    store = VectorStore()

    # Health check
    if store.health_check():
        print("Qdrant is healthy")
        info = store.get_collection_info()
        print(f"Collection info: {info}")
    else:
        print("Qdrant is not available")
