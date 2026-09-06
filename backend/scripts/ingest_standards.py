#!/usr/bin/env python3
"""
Ingestion script for Indian Standards data from CSV.

Reads the `indian_standards_cleaned.csv` file.
1. Generates semantic embeddings for the descriptions and upserts to Qdrant.
2. Saves the full metadata (including download_link) to PostgreSQL.
"""

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

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.standard import Standard
from app.services.ai_engine import AIEngine
from app.db.vector_store import VectorStore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_stable_id(standard_number: str) -> int:
    """Generate stable point ID for Qdrant from standard_number."""
    hash_obj = hashlib.md5(standard_number.encode())
    point_id = int(hash_obj.hexdigest()[:16], 16)
    return point_id % (2**31 - 1)

def load_csv(file_path: str) -> List[Dict[str, str]]:
    logger.info(f"Loading CSV file: {file_path}")
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('is_code') and row.get('description'):
                records.append(row)
    logger.info(f"Loaded {len(records)} records from CSV")
    return records

def ingest_standards(file_path: str, batch_size: int = 64):
    logger.info("Initializing AI Engine and Vector Store...")
    ai_engine = AIEngine()
    vector_store = VectorStore()
    
    logger.info(f"Ensuring Qdrant collection with dimension: {ai_engine.dimension}")
    vector_store.ensure_collection(ai_engine.dimension)

    records = load_csv(file_path)
    if not records:
        logger.error("No valid records found to ingest.")
        return

    # Process in batches
    db: Session = SessionLocal()
    try:
        upserted_qdrant = 0
        upserted_postgres = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            texts_to_embed = []
            qdrant_points = []
            postgres_objects = []

            # Prepare data
            for record in batch:
                is_code = record['is_code'].strip()
                description = record['description'].strip()
                download_link = record.get('download_link', '').strip()
                
                texts_to_embed.append(description)
                
                # Qdrant Point Prep
                qdrant_points.append({
                    "id": generate_stable_id(is_code),
                    # "vector": will be added after embedding
                    "payload": {
                        "standard_id": is_code,
                        "standard_number": is_code,
                        "title": description,  # CSV uses description as the title/scope
                        "description": description
                    }
                })

                # Postgres Object Prep
                postgres_objects.append(Standard(
                    id=is_code,
                    standard_number=is_code,
                    title=description,
                    description=description,
                    download_link=download_link
                ))

            # 1. Embed and Upsert to Qdrant
            logger.info(f"Embedding batch of {len(texts_to_embed)} records...")
            embeddings = ai_engine.embed_batch(texts_to_embed)
            for point, emb in zip(qdrant_points, embeddings):
                point["vector"] = emb
                
            vector_store.upsert(qdrant_points)
            upserted_qdrant += len(qdrant_points)

            # 2. Upsert to Postgres
            for std in postgres_objects:
                existing = db.query(Standard).filter(Standard.id == std.id).first()
                if not existing:
                    db.add(std)
                else:
                    existing.title = std.title
                    existing.description = std.description
                    existing.download_link = std.download_link
            
            db.commit()
            upserted_postgres += len(postgres_objects)

        logger.info("=" * 40)
        logger.info("INGESTION COMPLETE")
        logger.info(f"Qdrant Points Upserted: {upserted_qdrant}")
        logger.info(f"Postgres Rows Upserted: {upserted_postgres}")
        logger.info("=" * 40)

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest CSV data to Postgres & Qdrant")
    parser.add_argument("--input", required=True, help="Path to CSV file")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        logger.error(f"File not found: {args.input}")
        sys.exit(1)

    ingest_standards(args.input, args.batch_size)
