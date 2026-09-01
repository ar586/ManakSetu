"""
Tests for Vector Store integration with Qdrant.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.db.vector_store import VectorStore, SearchResult
from qdrant_client.models import PointIdsList


class TestVectorStoreInitialization:
    """Tests for VectorStore initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default configuration."""
        store = VectorStore()
        assert store.url == "http://localhost:6333"
        assert store.collection_name == "indian_standards"

    def test_initialization_with_custom_values(self):
        """Test initialization with custom URL and collection."""
        store = VectorStore(
            url="http://custom:6333",
            collection_name="custom_collection"
        )
        assert store.url == "http://custom:6333"
        assert store.collection_name == "custom_collection"


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating SearchResult."""
        result = SearchResult(
            point_id=1,
            score=0.95,
            standard_id="TEST-001",
            standard_number="TEST-STANDARD-001",
            title="Test Standard",
            payload={"key": "value"}
        )

        assert result.point_id == 1
        assert result.score == 0.95
        assert result.standard_id == "TEST-001"
        assert result.standard_number == "TEST-STANDARD-001"
        assert result.title == "Test Standard"
        assert result.payload == {"key": "value"}


class TestVectorStoreOperations:
    """Tests for Vector Store operations (mocked Qdrant)."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Qdrant client."""
        return MagicMock()

    @pytest.fixture
    def vector_store(self, mock_client):
        """Create Vector Store with mocked client."""
        store = VectorStore()
        store._client = mock_client
        return store

    def test_upsert_validation(self, vector_store):
        """Test validation in upsert."""
        # Empty list is a valid no-op: upsert([]) -> 0 (not an error). This
        # matches how the ingestion script calls upsert() on possibly-empty
        # batches without needing to special-case an exception.
        assert vector_store.upsert([]) == 0

        with pytest.raises(ValueError):
            vector_store.upsert("not a list")  # Invalid type

        with pytest.raises(ValueError):
            vector_store.upsert([{"id": 1, "vector": [0.1]}])  # Missing "payload" key

        with pytest.raises(ValueError):
            vector_store.upsert(["not a dict"])  # Point is not a dict

    def test_search_validation(self, vector_store):
        """Test validation in search."""
        with pytest.raises(ValueError):
            vector_store.search([])  # Empty vector

        with pytest.raises(ValueError):
            vector_store.search([1, 2, 3], top_k=-1)  # Invalid top_k

    def test_delete_validation(self, vector_store):
        """Test validation in delete."""
        # Empty list should not raise
        result = vector_store.delete([])
        assert result == 0

    @patch('app.db.vector_store.QdrantClient')
    def test_collection_ensure_create(self, mock_qdrant_class):
        """Test ensuring collection creates it if missing."""
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client

        # Mock get_collections to return empty
        mock_client.get_collections.return_value = MagicMock(collections=[])

        store = VectorStore()
        store.ensure_collection(vector_size=384)

        # Should call create_collection
        mock_client.create_collection.assert_called_once()

    @patch('app.db.vector_store.QdrantClient')
    def test_collection_ensure_recreate(self, mock_qdrant_class):
        """Test that recreate=True deletes and recreates an existing collection."""
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client

        existing_collection = MagicMock()
        existing_collection.name = "indian_standards"
        mock_client.get_collections.return_value = MagicMock(collections=[existing_collection])

        store = VectorStore()
        store.ensure_collection(vector_size=384, recreate=True)

        mock_client.delete_collection.assert_called_once_with("indian_standards")
        mock_client.create_collection.assert_called_once()

    def test_search_uses_query_points(self, vector_store, mock_client):
        """Test that search() calls the current query_points() API, not the
        legacy search() endpoint (removed in current Qdrant versions)."""
        fake_point = MagicMock()
        fake_point.id = 42
        fake_point.score = 0.87
        fake_point.payload = {
            "standard_id": "TEST-001",
            "standard_number": "TEST-STANDARD-001",
            "title": "Test Standard",
        }
        mock_client.query_points.return_value = MagicMock(points=[fake_point])

        results = vector_store.search([0.1, 0.2, 0.3], top_k=3, score_threshold=0.5)

        # The legacy endpoint must not be used.
        mock_client.search.assert_not_called()
        mock_client.query_points.assert_called_once()

        _, kwargs = mock_client.query_points.call_args
        assert kwargs["collection_name"] == vector_store.collection_name
        assert kwargs["query"] == [0.1, 0.2, 0.3]
        assert kwargs["limit"] == 3
        assert kwargs["score_threshold"] == 0.5

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, SearchResult)
        assert result.point_id == 42
        assert result.score == 0.87
        assert result.standard_id == "TEST-001"
        assert result.standard_number == "TEST-STANDARD-001"
        assert result.title == "Test Standard"

    def test_search_top_k_and_payload_retrieval(self, vector_store, mock_client):
        """Test that top_k limits results and payload is attached to each result."""
        points = []
        for i in range(3):
            p = MagicMock()
            p.id = i
            p.score = 1.0 - (i * 0.1)
            p.payload = {"standard_id": f"TEST-{i:03d}", "standard_number": "", "title": ""}
            points.append(p)
        mock_client.query_points.return_value = MagicMock(points=points)

        results = vector_store.search([0.1, 0.2], top_k=3)

        assert len(results) == 3
        assert all(isinstance(r, SearchResult) for r in results)
        assert all(r.payload for r in results)

    def test_delete_uses_point_ids_list_selector(self, vector_store, mock_client):
        """Test that delete() uses the current PointIdsList selector API
        rather than passing a raw list of IDs directly."""
        result = vector_store.delete([1, 2, 3])

        mock_client.delete.assert_called_once()
        _, kwargs = mock_client.delete.call_args
        assert kwargs["collection_name"] == vector_store.collection_name

        selector = kwargs["points_selector"]
        assert isinstance(selector, PointIdsList)
        assert selector.points == [1, 2, 3]
        assert result == 3

    def test_health_check(self, vector_store):
        """Test health check."""
        vector_store.client.get_collection.return_value = MagicMock()

        result = vector_store.health_check()
        assert result is True

    def test_health_check_failure(self, vector_store):
        """Test health check when Qdrant is unavailable."""
        vector_store.client.get_collection.side_effect = Exception("Connection failed")

        result = vector_store.health_check()
        assert result is False


class TestConfigurationEnvironmentVariables:
    """Tests for configuration from environment variables."""

    @patch.dict('os.environ', {
        'QDRANT_URL': 'http://custom-qdrant:6333',
        'QDRANT_COLLECTION': 'custom_standards',
        'VECTOR_SCORE_THRESHOLD': '0.5'
    })
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        from app.db.vector_store import get_qdrant_url, get_qdrant_collection, get_vector_score_threshold

        assert get_qdrant_url() == 'http://custom-qdrant:6333'
        assert get_qdrant_collection() == 'custom_standards'
        assert get_vector_score_threshold() == 0.5

    def test_default_configuration(self):
        """Test default configuration when env vars not set."""
        from app.db.vector_store import get_qdrant_url, get_qdrant_collection, get_vector_score_threshold

        url = get_qdrant_url()
        assert url == "http://localhost:6333"

        collection = get_qdrant_collection()
        assert collection == "indian_standards"

        threshold = get_vector_score_threshold()
        assert threshold == 0.0


class TestStablePointIdGeneration:
    """Tests for stable point ID generation for idempotent ingestion."""

    def test_stable_id_generation(self):
        """Test that same standard_id produces same point_id."""
        from scripts.ingest_standards import generate_stable_id

        id1 = generate_stable_id("TEST-001")
        id2 = generate_stable_id("TEST-001")

        assert id1 == id2

    def test_different_ids_for_different_standards(self):
        """Test that different standards get different point IDs."""
        from scripts.ingest_standards import generate_stable_id

        id1 = generate_stable_id("TEST-001")
        id2 = generate_stable_id("TEST-002")

        assert id1 != id2

    def test_stable_id_is_positive_integer(self):
        """Test that point ID is positive integer."""
        from scripts.ingest_standards import generate_stable_id

        point_id = generate_stable_id("TEST-001")

        assert isinstance(point_id, int)
        assert point_id > 0


class TestPointStructure:
    """Tests for Qdrant point structure."""

    def test_point_structure_validation(self):
        """Test that points have correct structure."""
        point = {
            "id": 12345,
            "vector": [0.1, 0.2, 0.3],  # Example embedding
            "payload": {
                "standard_id": "TEST-001",
                "standard_number": "TEST-STANDARD-001",
                "title": "Test Standard",
                "text": "Full text for embedding",
                "scope": "Scope of standard",
                "description": "Description",
            }
        }

        # Validate structure
        assert "id" in point
        assert "vector" in point
        assert "payload" in point
        assert isinstance(point["id"], int)
        assert isinstance(point["vector"], list)
        assert isinstance(point["payload"], dict)
        assert "standard_id" in point["payload"]
