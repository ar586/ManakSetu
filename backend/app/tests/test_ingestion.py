"""Tests for the current CSV-to-MiniLM-to-Qdrant ingestion pipeline."""

import csv
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import scripts.ingest_standards as ingestion


def write_csv(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    path = tmp_path / "standards.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["is_code", "description", "download_link"])
        writer.writeheader()
        writer.writerows(rows)
    return path


class FakeDatabase:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def query(self, _model):
        return self

    def filter(self, _criterion):
        return self

    def first(self):
        return None

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class FakeEmbeddingEngine:
    dimension = 3

    def __init__(self):
        self.batches = []

    def embed_batch(self, texts):
        self.batches.append(texts)
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeVectorStore:
    def __init__(self):
        self.ensure_calls = []
        self.upserted = []

    def ensure_collection(self, dimension, recreate=False):
        self.ensure_calls.append((dimension, recreate))

    def upsert(self, points):
        self.upserted.extend(points)
        return len(points)


def patch_dependencies(monkeypatch, engine=None, vector_store=None, database=None):
    engine = engine or FakeEmbeddingEngine()
    vector_store = vector_store or FakeVectorStore()
    database = database or FakeDatabase()
    monkeypatch.setattr(ingestion, "AIEngine", lambda: engine)
    monkeypatch.setattr(ingestion, "VectorStore", lambda: vector_store)
    monkeypatch.setattr(ingestion, "SessionLocal", lambda: database)
    return engine, vector_store, database


class TestCsvLoading:
    def test_load_csv_keeps_valid_unique_records(self, tmp_path):
        path = write_csv(tmp_path, [
            {"is_code": "IS 100:2020", "description": " First standard ", "download_link": ""},
            {"is_code": "IS 100:2020", "description": "duplicate", "download_link": ""},
            {"is_code": "", "description": "missing code", "download_link": ""},
            {"is_code": "IS 200:2021", "description": "Second standard", "download_link": ""},
        ])

        records = ingestion.load_csv(str(path))

        assert [record["is_code"] for record in records] == ["IS 100:2020", "IS 200:2021"]

    def test_load_csv_skips_empty_description(self, tmp_path):
        path = write_csv(tmp_path, [
            {"is_code": "IS 100:2020", "description": "", "download_link": ""},
        ])

        assert ingestion.load_csv(str(path)) == []


class TestStableIds:
    def test_same_chunk_key_is_idempotent(self):
        assert ingestion.generate_stable_id("IS 100:2020:0") == ingestion.generate_stable_id("IS 100:2020:0")

    def test_different_chunks_have_distinct_ids(self):
        assert ingestion.generate_stable_id("IS 100:2020:0") != ingestion.generate_stable_id("IS 100:2020:1")

    def test_ids_are_positive_integers(self):
        point_id = ingestion.generate_stable_id("IS 100:2020:0")
        assert isinstance(point_id, int)
        assert point_id > 0


class TestCurrentIngestion:
    def test_ingestion_batches_embeddings_and_upserts_chunk_payloads(self, tmp_path, monkeypatch):
        path = write_csv(tmp_path, [
            {"is_code": "IS 100:2020", "description": "Concrete requirements", "download_link": ""},
            {"is_code": "IS 200:2021", "description": "Steel requirements", "download_link": "https://example.test/is200"},
        ])
        engine, vector_store, database = patch_dependencies(monkeypatch)

        ingestion.ingest_standards(str(path), batch_size=1, recreate_collection=True)

        assert vector_store.ensure_calls == [(3, True)]
        assert len(engine.batches) == 2
        assert len(vector_store.upserted) == 2
        point = vector_store.upserted[0]
        assert point["vector"] == [0.1, 0.2, 0.3]
        assert point["payload"]["standard_id"] == "IS 100:2020"
        assert point["payload"]["chunk_id"] == "IS 100:2020:0"
        assert point["payload"]["source_document"] == path.name
        assert len(database.added) == 2
        assert database.commits == 2
        assert database.closed is True

    def test_recreate_collection_defaults_to_false(self, tmp_path, monkeypatch):
        path = write_csv(tmp_path, [
            {"is_code": "IS 100:2020", "description": "Concrete requirements", "download_link": ""},
        ])
        _, vector_store, _ = patch_dependencies(monkeypatch)

        ingestion.ingest_standards(str(path))

        assert vector_store.ensure_calls == [(3, False)]

    def test_embedding_failure_rolls_back_and_does_not_upsert(self, tmp_path, monkeypatch):
        path = write_csv(tmp_path, [
            {"is_code": "IS 100:2020", "description": "Concrete requirements", "download_link": ""},
        ])
        engine = MagicMock(dimension=3)
        engine.embed_batch.side_effect = RuntimeError("embedding failed")
        _, vector_store, database = patch_dependencies(monkeypatch, engine=engine)

        with pytest.raises(SystemExit) as error:
            ingestion.ingest_standards(str(path))

        assert error.value.code == 1
        assert vector_store.upserted == []
        assert database.rollbacks == 1
        assert database.closed is True

    def test_qdrant_failure_rolls_back(self, tmp_path, monkeypatch):
        path = write_csv(tmp_path, [
            {"is_code": "IS 100:2020", "description": "Concrete requirements", "download_link": ""},
        ])
        vector_store = MagicMock()
        vector_store.upsert.side_effect = RuntimeError("qdrant unavailable")
        _, _, database = patch_dependencies(monkeypatch, vector_store=vector_store)

        with pytest.raises(SystemExit) as error:
            ingestion.ingest_standards(str(path))

        assert error.value.code == 1
        assert database.rollbacks == 1
        assert database.closed is True
