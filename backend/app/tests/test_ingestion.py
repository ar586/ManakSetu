"""
Tests for ingestion pipeline.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from scripts.ingest_standards import (
    validate_standard_record,
    load_json_file,
    load_csv_file,
    load_standards_file,
    generate_stable_id,
    ingest_standards,
)
from app.services.ai_engine import AIEngine
from app.db.vector_store import VectorStore


class TestRecordValidation:
    """Tests for standard record validation."""

    def test_valid_record(self, sample_standard_record):
        """Test validation of valid record."""
        is_valid, error = validate_standard_record(sample_standard_record, 0)
        assert is_valid is True
        assert error is None

    def test_missing_required_field(self):
        """Test validation of record with missing required field."""
        record = {
            "standard_id": "TEST-001",
            "standard_number": "TEST-STANDARD-001",
            "title": "Test",
            # Missing 'scope'
        }
        is_valid, error = validate_standard_record(record, 0)
        assert is_valid is False
        assert "scope" in error.lower()

    def test_empty_required_field(self):
        """Test validation of record with empty required field."""
        record = {
            "standard_id": "TEST-001",
            "standard_number": "TEST-STANDARD-001",
            "title": "Test",
            "scope": ""  # Empty
        }
        is_valid, error = validate_standard_record(record, 0)
        assert is_valid is False
        assert "empty" in error.lower()


class TestJsonLoading:
    """Tests for JSON file loading."""

    def test_load_valid_json(self, sample_standards_list):
        """Test loading valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_standards_list, f)
            f.flush()
            temp_path = f.name

        try:
            records = load_json_file(temp_path)
            assert len(records) == len(sample_standards_list)
            assert records[0]["standard_id"] == "TEST-001"
        finally:
            Path(temp_path).unlink()

    def test_load_single_object_json(self, sample_standard_record):
        """Test loading JSON with single object."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_standard_record, f)
            f.flush()
            temp_path = f.name

        try:
            records = load_json_file(temp_path)
            assert len(records) == 1
            assert records[0]["standard_id"] == sample_standard_record["standard_id"]
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_json(self):
        """Test loading non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            load_json_file("/nonexistent/path/file.json")


class TestCsvLoading:
    """Tests for CSV file loading."""

    def test_load_valid_csv(self, sample_standards_list):
        """Test loading valid CSV file."""
        import csv

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'standard_id', 'standard_number', 'title', 'scope', 'description'
            ])
            writer.writeheader()
            for record in sample_standards_list:
                writer.writerow(record)
            f.flush()
            temp_path = f.name

        try:
            records = load_csv_file(temp_path)
            assert len(records) == len(sample_standards_list)
            assert records[0]["standard_id"] == "TEST-001"
        finally:
            Path(temp_path).unlink()

    def test_load_csv_missing_required_columns(self):
        """Test loading CSV with missing required columns."""
        import csv

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'scope'])
            writer.writeheader()
            writer.writerow({'title': 'Test', 'scope': 'Test scope'})
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_csv_file(temp_path)
        finally:
            Path(temp_path).unlink()


class TestUniversalFileLoading:
    """Tests for universal file loading."""

    def test_load_json_file_extension(self, sample_standards_list):
        """Test loading JSON by file extension."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_standards_list, f)
            f.flush()
            temp_path = f.name

        try:
            records = load_standards_file(temp_path)
            assert len(records) == len(sample_standards_list)
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_standards_file("/nonexistent/file.json")

    def test_load_unsupported_format(self):
        """Test loading unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Some text")
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_standards_file(temp_path)
        finally:
            Path(temp_path).unlink()


class TestIngestionStatistics:
    """Tests that ingestion statistics accurately reflect failures rather
    than silently dropping records from the counts."""

    @pytest.fixture
    def temp_json_file(self, sample_standards_list):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_standards_list, f)
            f.flush()
            temp_path = f.name
        yield temp_path
        Path(temp_path).unlink()

    def test_total_embedding_failure_reported_as_failed_not_hidden(self, temp_json_file):
        """
        If embedding fails for the entire batch of otherwise-valid records,
        those records must be counted in failed_records - not silently
        vanish (embedded_records=0, failed_records=0, which would look like
        nothing happened).
        """
        fake_ai_engine = MagicMock(spec=AIEngine)
        fake_ai_engine.dimension = 8
        fake_ai_engine.embed_batch.side_effect = RuntimeError("simulated embedding failure")

        fake_vector_store = MagicMock(spec=VectorStore)

        stats = ingest_standards(
            temp_json_file,
            vector_store=fake_vector_store,
            ai_engine=fake_ai_engine,
        )

        assert stats["valid_records"] == 3
        assert stats["embedded_records"] == 0
        assert stats["upserted_records"] == 0
        assert stats["failed_records"] == 3

        # Qdrant must never be told to upsert points that were never embedded.
        fake_vector_store.upsert.assert_not_called()

    def test_partial_upsert_batch_failure_reported_accurately(self, temp_json_file):
        """
        If embedding succeeds but one Qdrant upsert batch fails, only the
        records in that batch should be counted as failed - the rest should
        still be counted as upserted.
        """
        fake_ai_engine = MagicMock(spec=AIEngine)
        fake_ai_engine.dimension = 8
        fake_ai_engine.embed_batch.side_effect = lambda texts, **kw: [
            [0.1] * 8 for _ in texts
        ]

        fake_vector_store = MagicMock(spec=VectorStore)
        # 3 records, batch_size=2 -> two upsert calls: [2 records], [1 record].
        # First call succeeds, second fails.
        fake_vector_store.upsert.side_effect = [2, RuntimeError("Qdrant unavailable")]

        stats = ingest_standards(
            temp_json_file,
            batch_size=2,
            vector_store=fake_vector_store,
            ai_engine=fake_ai_engine,
        )

        assert stats["embedded_records"] == 3
        assert stats["upserted_records"] == 2
        assert stats["failed_records"] == 1


class TestStableIdGeneration:
    """Tests for stable point ID generation."""

    def test_stable_id_reproducibility(self):
        """Test that same standard_id always produces same point_id."""
        id1 = generate_stable_id("TEST-001")
        id2 = generate_stable_id("TEST-001")
        assert id1 == id2

    def test_different_ids_for_different_standards(self):
        """Test that different standards get different IDs."""
        id1 = generate_stable_id("TEST-001")
        id2 = generate_stable_id("TEST-002")
        assert id1 != id2

    def test_point_id_is_positive(self):
        """Test that point ID is positive."""
        point_id = generate_stable_id("TEST-001")
        assert isinstance(point_id, int)
        assert point_id > 0

    def test_idempotent_ingestion_same_id(self):
        """Test that re-ingesting same standard produces same point ID."""
        standard_id = "TEST-001"

        # First ingestion
        id1 = generate_stable_id(standard_id)

        # Second ingestion (simulated)
        id2 = generate_stable_id(standard_id)

        # Should be identical for idempotent upsert
        assert id1 == id2
