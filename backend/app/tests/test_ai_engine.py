"""
Tests for AI Engine embedding service.

Split into two parts:

1. Offline unit tests (default `pytest` run). These mock the underlying
   sentence-transformers model so they exercise AIEngine's own logic
   (validation, batching contract, caching, configurable batch size,
   normalization handling) without requiring network access or a real
   model download.

2. Real-model integration tests (`TestRealModelIntegration`), which load the
   actual configured sentence-transformers model to verify genuine semantic
   behavior (e.g. related texts scoring higher similarity than unrelated
   ones). These require downloading the model from huggingface.co on first
   run and are automatically skipped (not silently passed) if that model
   cannot be loaded - e.g. no network access, as in this offline sandbox.
"""

import math
import zlib

import numpy as np
import pytest

import app.services.ai_engine as ai_engine_module
from app.services.ai_engine import AIEngine, embed, embed_batch, get_dimension


# ---------------------------------------------------------------------------
# Offline mock for sentence-transformers
# ---------------------------------------------------------------------------

_FAKE_DIM = 384


def _deterministic_vector(text: str, dim: int = _FAKE_DIM) -> np.ndarray:
    """Deterministic pseudo-embedding derived from text content (not semantic)."""
    seed = zlib.adler32(text.encode("utf-8")) & 0xFFFFFFFF
    rng = np.random.RandomState(seed)
    return rng.normal(size=dim)


class _FakeSentenceTransformer:
    """
    Offline stand-in for sentence_transformers.SentenceTransformer.

    Produces deterministic, L2-normalized vectors keyed off text content so
    that repeated calls with the same text return the same vector, and
    single-text vs batch encoding stay consistent with each other. It does
    NOT model real semantic similarity - tests relying on semantic quality
    belong in TestRealModelIntegration below, not here.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name

    def get_sentence_embedding_dimension(self) -> int:
        return _FAKE_DIM

    def encode(
        self,
        inputs,
        batch_size: int = 32,
        convert_to_tensor: bool = False,
        normalize_embeddings: bool = True,
        show_progress_bar: bool = False,
    ):
        is_single = isinstance(inputs, str)
        texts = [inputs] if is_single else list(inputs)

        vectors = np.array([_deterministic_vector(t) for t in texts])

        if normalize_embeddings:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            vectors = vectors / norms

        return vectors[0] if is_single else vectors


@pytest.fixture(autouse=True)
def mock_model(monkeypatch):
    """
    Patch sentence_transformers.SentenceTransformer with the offline fake for
    every test in this module, and reset AIEngine's module-level model cache
    before and after each test so tests don't leak state into each other.
    """
    monkeypatch.setattr(ai_engine_module, "SentenceTransformer", _FakeSentenceTransformer)
    ai_engine_module._model_cache = None
    ai_engine_module._model_name_cache = None
    ai_engine_module._engine_instance = None
    yield
    ai_engine_module._model_cache = None
    ai_engine_module._model_name_cache = None
    ai_engine_module._engine_instance = None


class TestAIEngine:
    """Tests for AIEngine class."""

    @pytest.fixture
    def engine(self):
        """Create AIEngine instance."""
        return AIEngine()

    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None

    def test_model_loading(self, engine):
        """Test model loading."""
        model = engine.model
        assert model is not None

    def test_model_is_cached(self, engine):
        """Test that the model is loaded once and reused (not reloaded)."""
        model1 = engine.model
        model2 = engine.model
        assert model1 is model2

    def test_embedding_dimension(self, engine):
        """Test getting embedding dimension."""
        dim = engine.dimension
        assert isinstance(dim, int)
        assert dim > 0
        assert dim == _FAKE_DIM


class TestSingleEmbedding:
    """Tests for single text embedding."""

    @pytest.fixture
    def engine(self):
        return AIEngine()

    def test_single_embedding(self, engine):
        """Test generating single embedding."""
        text = "LED street lighting for outdoor road"
        embedding = engine.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == engine.dimension
        assert all(isinstance(x, float) for x in embedding)

    def test_normalized_embedding(self, engine):
        """Test that embedding is normalized."""
        text = "Test text"
        embedding = engine.embed(text)

        norm = math.sqrt(sum(x**2 for x in embedding))

        # Should be close to 1.0 for normalized vectors
        assert abs(norm - 1.0) < 0.01

    def test_empty_input_rejection(self, engine):
        """Test rejection of empty input."""
        with pytest.raises(ValueError):
            engine.embed("")

    def test_whitespace_only_rejection(self, engine):
        """Test rejection of whitespace-only input."""
        with pytest.raises(ValueError):
            engine.embed("   \n\t  ")

    def test_invalid_type_rejection(self, engine):
        """Test rejection of invalid type."""
        with pytest.raises(ValueError):
            engine.embed(123)

    def test_consistent_embeddings(self, engine):
        """Test that same text produces same embedding."""
        text = "Consistent embedding test"
        embedding1 = engine.embed(text)
        embedding2 = engine.embed(text)

        assert embedding1 == embedding2


class TestBatchEmbedding:
    """Tests for batch embedding."""

    @pytest.fixture
    def engine(self):
        return AIEngine()

    def test_batch_embedding(self, engine):
        """Test batch embedding."""
        texts = [
            "LED street lighting",
            "Safety requirements for electrical equipment",
            "Concrete specifications for construction"
        ]

        embeddings = engine.embed_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)
        assert all(len(e) == engine.dimension for e in embeddings)

    def test_batch_empty_list(self, engine):
        """Test batch with empty list."""
        with pytest.raises(ValueError):
            engine.embed_batch([])

    def test_batch_invalid_type(self, engine):
        """Test batch rejects non-list input."""
        with pytest.raises(ValueError):
            engine.embed_batch("not a list")

    def test_batch_consistency(self, engine):
        """Test that batch and single embeddings are consistent."""
        text = "Test text for consistency"

        single = engine.embed(text)
        batch = engine.embed_batch([text])[0]

        assert len(single) == len(batch)
        for s, b in zip(single, batch):
            assert abs(s - b) < 0.001

    def test_batch_rejects_invalid_input_without_dropping(self, engine):
        """
        Test the safe batch contract: a batch containing an invalid entry
        (empty string) must raise ValueError for the whole batch rather than
        silently dropping the bad entry, which would misalign the returned
        embeddings with the caller's original list/records.
        """
        texts = ["LED street light", "", "road lighting"]

        with pytest.raises(ValueError):
            engine.embed_batch(texts)

    def test_batch_rejects_whitespace_only_entry(self, engine):
        """Test that a whitespace-only entry anywhere in the batch is rejected."""
        texts = ["Valid text", "   ", "Another valid text"]

        with pytest.raises(ValueError):
            engine.embed_batch(texts)

    def test_batch_does_not_mutate_caller_list(self, engine):
        """Test that a failed batch call leaves the caller's list untouched."""
        texts = ["LED street light", "", "road lighting"]
        original = list(texts)

        with pytest.raises(ValueError):
            engine.embed_batch(texts)

        assert texts == original

    def test_batch_output_order_matches_input_order(self, engine):
        """Test that embeddings are returned in the same order as the input texts."""
        texts = ["alpha text", "beta text", "gamma text"]
        embeddings = engine.embed_batch(texts)

        # Each embedding should match embedding a single one of the same text.
        for text, embedding in zip(texts, embeddings):
            single = engine.embed(text)
            assert embedding == single


class TestConfigurableEmbeddingBatchSize:
    """Tests for the configurable EMBEDDING_BATCH_SIZE."""

    @pytest.fixture
    def engine(self):
        return AIEngine()

    def test_default_batch_size(self):
        """Test default embedding batch size when env var not set."""
        assert ai_engine_module.get_embedding_batch_size() == 32

    def test_custom_batch_size_from_env(self, monkeypatch):
        """Test batch size is read from EMBEDDING_BATCH_SIZE env var."""
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "8")
        assert ai_engine_module.get_embedding_batch_size() == 8

    def test_invalid_batch_size_env_falls_back_to_default(self, monkeypatch):
        """Test a non-integer EMBEDDING_BATCH_SIZE falls back to the default."""
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "not-a-number")
        assert ai_engine_module.get_embedding_batch_size() == 32

    def test_non_positive_batch_size_env_falls_back_to_default(self, monkeypatch):
        """Test a non-positive EMBEDDING_BATCH_SIZE falls back to the default."""
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "0")
        assert ai_engine_module.get_embedding_batch_size() == 32

    def test_configured_batch_size_is_actually_used(self, engine, monkeypatch):
        """
        Test that the encode() call actually receives the configured batch
        size, rather than the config being decorative.
        """
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "2")

        captured = {}
        model = engine.model
        original_encode = model.encode

        def spy_encode(inputs, **kwargs):
            captured["batch_size"] = kwargs.get("batch_size")
            return original_encode(inputs, **kwargs)

        model.encode = spy_encode

        engine.embed_batch(["text one", "text two", "text three"])

        assert captured["batch_size"] == 2

    def test_explicit_batch_size_overrides_env(self, engine, monkeypatch):
        """Test that an explicit batch_size argument overrides the env var."""
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "2")

        captured = {}
        model = engine.model
        original_encode = model.encode

        def spy_encode(inputs, **kwargs):
            captured["batch_size"] = kwargs.get("batch_size")
            return original_encode(inputs, **kwargs)

        model.encode = spy_encode

        engine.embed_batch(["text one", "text two"], batch_size=16)

        assert captured["batch_size"] == 16

    def test_embedding_batch_size_distinct_from_qdrant_batch_size(self, monkeypatch):
        """
        Test that EMBEDDING_BATCH_SIZE and QDRANT_BATCH_SIZE are independent
        settings - setting one must not affect the other.
        """
        monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "4")
        monkeypatch.delenv("QDRANT_BATCH_SIZE", raising=False)

        assert ai_engine_module.get_embedding_batch_size() == 4
        # QDRANT_BATCH_SIZE is a separate concept consumed by the ingestion
        # script's `--batch-size` argument, not read by ai_engine at all.
        import os
        assert os.getenv("QDRANT_BATCH_SIZE") is None


class TestSimilarity:
    """Tests for similarity calculation (math only - see TestRealModelIntegration
    for tests that depend on genuine semantic quality)."""

    @pytest.fixture
    def engine(self):
        return AIEngine()

    def test_similarity_identical_vectors(self, engine):
        """Test similarity of identical vectors."""
        text = "Test text"
        embedding = engine.embed(text)

        similarity = engine.similarity(embedding, embedding)
        assert abs(similarity - 1.0) < 0.001

    def test_similarity_range(self, engine):
        """Test similarity is in valid range."""
        text1 = "LED street lighting"
        text2 = "Safety equipment requirements"

        emb1 = engine.embed(text1)
        emb2 = engine.embed(text2)

        similarity = engine.similarity(emb1, emb2)
        assert 0.0 <= similarity <= 1.0


class TestMultilingualEmbedding:
    """Tests that multilingual (Unicode) input is accepted and embedded
    mechanically - see TestRealModelIntegration for genuine cross-lingual
    semantic similarity, which requires the real model."""

    @pytest.fixture
    def engine(self):
        return AIEngine()

    def test_hindi_embedding(self, engine, hindi_text):
        """Test embedding Hindi text."""
        embedding = engine.embed(hindi_text)

        assert isinstance(embedding, list)
        assert len(embedding) == engine.dimension

    def test_english_embedding(self, engine):
        """Test embedding English text."""
        text = "90W LED street light for road lighting"
        embedding = engine.embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) == engine.dimension


class TestModuleConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_embed_function(self):
        """Test module-level embed function."""
        text = "Test text"
        embedding = embed(text)

        assert isinstance(embedding, list)
        assert len(embedding) > 0

    def test_embed_batch_function(self):
        """Test module-level embed_batch function."""
        texts = ["Text 1", "Text 2"]
        embeddings = embed_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == len(texts)

    def test_get_dimension_function(self):
        """Test module-level get_dimension function."""
        dim = get_dimension()

        assert isinstance(dim, int)
        assert dim > 0


class TestValidation:
    """Tests for input validation."""

    @pytest.fixture
    def engine(self):
        return AIEngine()

    def test_validate_input_static_method(self, engine):
        """Test input validation."""
        is_valid, error = engine._validate_input("Valid text")
        assert is_valid is True
        assert error is None

        is_valid, error = engine._validate_input("")
        assert is_valid is False
        assert error is not None


# ---------------------------------------------------------------------------
# Real-model integration tests
# ---------------------------------------------------------------------------
#
# These tests intentionally bypass the `mock_model` autouse fixture's mock
# object (by restoring the real SentenceTransformer) and load the actual
# configured embedding model. This requires downloading model weights from
# huggingface.co on first use. If the model cannot be loaded - e.g. no
# network access - the class is skipped with an explicit reason rather than
# being silently reported as passed.


def _real_engine_or_skip():
    """
    Attempt to build an AIEngine backed by the real sentence-transformers
    model. Skips the calling test (with an explicit reason) if the model
    cannot be loaded, instead of letting the test fail or fabricating a pass.
    """
    import importlib
    real_module = importlib.import_module("sentence_transformers")
    ai_engine_module.SentenceTransformer = real_module.SentenceTransformer
    ai_engine_module._model_cache = None
    ai_engine_module._model_name_cache = None

    engine = AIEngine()
    try:
        _ = engine.dimension  # forces model load
    except Exception as e:
        pytest.skip(f"Real embedding model unavailable in this environment: {e}")
    return engine


@pytest.mark.integration
class TestRealModelIntegration:
    """
    Integration tests against the real configured sentence-transformers
    model. Separate from the offline unit tests above; skipped automatically
    if the model can't be downloaded/loaded (e.g. no internet access).
    """

    def test_similarity_related_texts(self):
        """Related texts should have higher similarity than unrelated ones."""
        engine = _real_engine_or_skip()

        text1 = "LED street lighting for road"
        text2 = "LED lighting for outdoor roads"
        text3 = "Concrete specifications for construction"

        emb1 = engine.embed(text1)
        emb2 = engine.embed(text2)
        emb3 = engine.embed(text3)

        sim_related = engine.similarity(emb1, emb2)
        sim_unrelated = engine.similarity(emb1, emb3)

        assert sim_related > sim_unrelated

    def test_multilingual_similarity(self, hindi_text):
        """Hindi and English descriptions of the same product should show
        meaningful cross-lingual similarity with the real multilingual model."""
        engine = _real_engine_or_skip()

        english = "90W LED street light for road"

        emb_hindi = engine.embed(hindi_text)
        emb_english = engine.embed(english)

        similarity = engine.similarity(emb_hindi, emb_english)

        assert similarity > 0.0
