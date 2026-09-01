#!/usr/bin/env python3
"""
Ingestion script for Indian Standards data.

Processes CSV/JSON files containing standards metadata.
Applies text preprocessing, generates embeddings, and loads into Qdrant.

Usage:
    python scripts/ingest_standards.py --input data/sample/synthetic_standards.json
    python scripts/ingest_standards.py --input data/standards.csv
"""

import json
import csv
import logging
import argparse
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ai_engine import AIEngine
from app.db.vector_store import VectorStore
from app.utils.text_processing import (
    clean_text,
    clean_product_description,
    build_standard_text,
    validate_text_for_embedding,
    normalize_standard_number
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_stable_id(standard_id: str) -> int:
    """
    Generate stable point ID from standard_id.

    Uses hash to ensure same standard_id always produces same point_id.
    This ensures idempotent ingestion.

    Args:
        standard_id: Unique standard identifier

    Returns:
        Integer point ID
    """
    # Hash the ID and convert to positive integer
    hash_obj = hashlib.md5(standard_id.encode())
    # Take first 8 bytes of hash
    point_id = int(hash_obj.hexdigest()[:16], 16)
    # Ensure it's positive and within reasonable range
    return point_id % (2**31 - 1)


def validate_standard_record(record: Dict[str, Any], index: int) -> tuple[bool, Optional[str]]:
    """
    Validate a standard record has required fields.

    Required fields:
    - standard_id
    - standard_number
    - title
    - scope

    Args:
        record: Standard record dictionary
        index: Record index in file

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["standard_id", "standard_number", "title", "scope"]

    for field in required_fields:
        if field not in record:
            return False, f"Missing required field: {field}"

        value = record[field]
        if not value or (isinstance(value, str) and not value.strip()):
            return False, f"Field '{field}' is empty"

    return True, None


def load_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load standards from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        List of standard records

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    logger.info(f"Loading JSON file: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    logger.info(f"Loaded {len(data)} records from JSON")
    return data


def load_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load standards from CSV file.

    Expected columns:
    - standard_id
    - standard_number
    - title
    - scope
    - description (optional)
    - sector (optional)
    - status (optional)
    - publication_year (optional)
    - latest_revision (optional)

    Args:
        file_path: Path to CSV file

    Returns:
        List of standard records

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns missing
    """
    logger.info(f"Loading CSV file: {file_path}")

    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError("CSV file is empty")

        # Check required columns
        required = {"standard_id", "standard_number", "title", "scope"}
        present = set(reader.fieldnames)

        if not required.issubset(present):
            missing = required - present
            raise ValueError(f"Missing required columns: {missing}")

        for row in reader:
            # Filter out empty fields
            record = {k: v for k, v in row.items() if v and v.strip()}
            records.append(record)

    logger.info(f"Loaded {len(records)} records from CSV")
    return records


def load_standards_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load standards from JSON or CSV file.

    Args:
        file_path: Path to standards file

    Returns:
        List of standard records

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format not supported
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".json":
        return load_json_file(file_path)
    elif suffix == ".csv":
        return load_csv_file(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def process_standards(
    records: List[Dict[str, Any]],
    ai_engine: AIEngine
) -> tuple[List[Dict[str, Any]], int, int]:
    """
    Process standards: validate, clean, embed.

    Args:
        records: Raw standard records
        ai_engine: Embedding service

    Returns:
        Tuple of (processed_points, valid_count, skipped_count)
    """
    points = []
    valid_count = 0
    skipped_count = 0

    logger.info(f"Processing {len(records)} records...")

    # Collect texts for batch embedding
    texts_to_embed = []
    text_to_record = {}  # Map text to record for later association

    for i, record in enumerate(records):
        # Validate record
        is_valid, error_msg = validate_standard_record(record, i)
        if not is_valid:
            logger.warning(f"Skipping record {i}: {error_msg}")
            skipped_count += 1
            continue

        try:
            # Clean fields
            standard_id = record["standard_id"].strip()
            standard_number = normalize_standard_number(record["standard_number"])
            title = clean_text(record["title"])
            scope = clean_text(record["scope"])
            description = clean_text(record.get("description", ""))

            # Build embedding text
            embedding_text = build_standard_text(title, scope, description)

            # Validate embedding text
            is_valid_text, error_msg = validate_text_for_embedding(embedding_text)
            if not is_valid_text:
                logger.warning(f"Record {i} (ID: {standard_id}): {error_msg}")
                skipped_count += 1
                continue

            # Prepare for batch embedding
            texts_to_embed.append(embedding_text)
            text_to_record[len(texts_to_embed) - 1] = {
                "standard_id": standard_id,
                "standard_number": standard_number,
                "title": title,
                "scope": scope,
                "description": description,
                "embedding_text": embedding_text,
                "sector": record.get("sector", ""),
                "status": record.get("status", ""),
                "publication_year": record.get("publication_year", ""),
                "latest_revision": record.get("latest_revision", ""),
            }
            valid_count += 1

        except Exception as e:
            logger.error(f"Error processing record {i}: {e}")
            skipped_count += 1

    logger.info(f"Valid records: {valid_count}, Skipped: {skipped_count}")

    if not texts_to_embed:
        logger.warning("No valid records to embed")
        return points, valid_count, skipped_count

    # Batch embed all texts
    logger.info(f"Generating embeddings for {len(texts_to_embed)} texts...")
    try:
        embeddings = ai_engine.embed_batch(texts_to_embed, show_progress_bar=True)
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return points, valid_count, skipped_count

    # Create Qdrant points
    for i, embedding in enumerate(embeddings):
        metadata = text_to_record[i]

        point = {
            "id": generate_stable_id(metadata["standard_id"]),
            "vector": embedding,
            "payload": {
                "standard_id": metadata["standard_id"],
                "standard_number": metadata["standard_number"],
                "title": metadata["title"],
                "text": metadata["embedding_text"],
                "scope": metadata["scope"],
                "description": metadata["description"],
                "sector": metadata["sector"],
                "status": metadata["status"],
                "publication_year": metadata["publication_year"],
                "latest_revision": metadata["latest_revision"],
            }
        }
        points.append(point)

    logger.info(f"Created {len(points)} Qdrant points")
    return points, valid_count, skipped_count


def ingest_standards(
    file_path: str,
    batch_size: int = 64,
    vector_store: Optional[VectorStore] = None,
    ai_engine: Optional[AIEngine] = None
) -> Dict[str, Any]:
    """
    Complete ingestion pipeline.

    Args:
        file_path: Path to standards file
        batch_size: Batch size for Qdrant upsert
        vector_store: VectorStore instance (creates if None)
        ai_engine: AIEngine instance (creates if None)

    Returns:
        Dictionary with ingestion statistics
    """
    if ai_engine is None:
        ai_engine = AIEngine()
    if vector_store is None:
        vector_store = VectorStore()

    stats = {
        "file_path": file_path,
        "total_records": 0,
        "valid_records": 0,
        "skipped_records": 0,
        "embedded_records": 0,
        "upserted_records": 0,
        "failed_records": 0,
        "start_time": time.time(),
    }

    try:
        # Load standards
        logger.info("=" * 60)
        logger.info("STANDARDS INGESTION PIPELINE")
        logger.info("=" * 60)

        records = load_standards_file(file_path)
        stats["total_records"] = len(records)

        # Ensure Qdrant collection
        logger.info(f"Ensuring Qdrant collection with dimension: {ai_engine.dimension}")
        vector_store.ensure_collection(ai_engine.dimension)

        # Process standards
        points, valid_count, skipped_count = process_standards(records, ai_engine)

        stats["valid_records"] = valid_count
        stats["skipped_records"] = skipped_count
        stats["embedded_records"] = len(points)

        # If records passed validation (valid_count > 0) but no points came
        # out of process_standards, embedding must have failed for the whole
        # batch (see process_standards' except clause). Without this, those
        # records would silently disappear from the statistics instead of
        # being counted as failures.
        if valid_count > 0 and not points:
            logger.error(
                f"Embedding failed for all {valid_count} valid record(s); "
                f"reporting them as failed rather than silently dropping them."
            )
            stats["failed_records"] += valid_count

        # Upsert to Qdrant in batches
        if points:
            logger.info(f"Upserting to Qdrant in batches of {batch_size}...")
            upserted = 0

            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                try:
                    batch_count = vector_store.upsert(batch)
                    upserted += batch_count
                except Exception as e:
                    logger.error(f"Batch upsert failed: {e}")
                    stats["failed_records"] += len(batch)

            stats["upserted_records"] = upserted

        # Final summary
        stats["end_time"] = time.time()
        stats["duration_seconds"] = stats["end_time"] - stats["start_time"]

        logger.info("=" * 60)
        logger.info("INGESTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records: {stats['total_records']}")
        logger.info(f"Valid records: {stats['valid_records']}")
        logger.info(f"Skipped records: {stats['skipped_records']}")
        logger.info(f"Embedded records: {stats['embedded_records']}")
        logger.info(f"Upserted records: {stats['upserted_records']}")
        logger.info(f"Failed records: {stats['failed_records']}")
        logger.info(f"Duration: {stats['duration_seconds']:.2f} seconds")
        logger.info("=" * 60)

        return stats

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        stats["error"] = str(e)
        return stats


def main():
    """Command-line interface for ingestion."""
    parser = argparse.ArgumentParser(
        description="Ingest Indian Standards into vector store"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to standards file (JSON or CSV)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for Qdrant upsert"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear collection before ingestion"
    )
    parser.add_argument(
        "--url",
        help="Qdrant server URL"
    )
    parser.add_argument(
        "--collection",
        help="Collection name"
    )

    args = parser.parse_args()

    # Validate input file
    if not Path(args.input).exists():
        logger.error(f"File not found: {args.input}")
        sys.exit(1)

    # Create vector store
    vector_store = VectorStore(url=args.url, collection_name=args.collection)

    # Clear if requested
    if args.clear:
        logger.warning("Clearing collection as requested")
        try:
            vector_store.clear_collection()
        except Exception as e:
            logger.warning(f"Collection clear requested but failed: {e}")

    # Run ingestion
    stats = ingest_standards(
        args.input,
        batch_size=args.batch_size,
        vector_store=vector_store
    )

    # Exit with appropriate code
    if stats.get("error"):
        sys.exit(1)

    if stats.get("upserted_records", 0) > 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
