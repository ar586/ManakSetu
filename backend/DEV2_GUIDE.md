# Developer 2: AI & Vector Store Implementation Guide

## Overview

Developer 2 is responsible for the semantic search infrastructure that powers ManakAI's standard recommendations. This includes text processing, multilingual embeddings, Qdrant vector database integration, and a complete ingestion pipeline.

## Architecture

```
                USER QUERY
                    |
                    v
         ┌──────────────────────┐
         │ text_processing.py   │
         │                      │
         │ Clean & normalize    │
         └──────────┬───────────┘
                    |
                    v
         ┌──────────────────────┐
         │   ai_engine.py       │
         │                      │
         │ Multilingual         │
         │ embeddings           │
         └──────────┬───────────┘
                    |
                    v
             QUERY VECTOR
                    |
                    v
         ┌──────────────────────┐
         │ vector_store.py      │
         │                      │
         │ Qdrant semantic      │
         │ search               │
         └──────────┬───────────┘
                    |
                    v
                QDRANT DB
                    |
                    v
            TOP-K RESULTS
                    |
                    v
         Developer 3 (Search Service)
```

## Implementation Status

### ✓ Completed Components

1. **app/utils/text_processing.py** - Text cleaning and preprocessing
2. **app/services/ai_engine.py** - Multilingual embedding generation
3. **app/db/vector_store.py** - Qdrant vector store abstraction
4. **scripts/ingest_standards.py** - Standards ingestion pipeline
5. **data/sample/synthetic_standards.json** - Synthetic test dataset (15 records)
6. **data/sample/eval_queries.json** - Evaluation queries
7. **app/services/evaluation.py** - Retrieval evaluation utilities
8. **app/tests/** - Comprehensive test suite

## Key Features

### Text Processing
- Preserves technical specifications (IP65, 90W, IS 302, etc.)
- Supports multilingual input (English, Hindi, etc.)
- Unicode normalization
- Technical identifier preservation
- Text chunking for long documents

### AI Engine
- Multilingual sentence-transformers model
- Single and batch embedding generation
- Model cached for performance
- Normalized L2 embeddings
- Input validation

### Vector Store
- Qdrant integration via qdrant-client
- Automatic collection creation
- Batch upsert operations
- Similarity search with configurable threshold
- Stable point IDs for idempotent ingestion

### Ingestion Pipeline
- CSV and JSON file support
- Record validation
- Batch processing
- Idempotent upsert (re-ingestion safe)
- Comprehensive logging

## Environment Variables

```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=indian_standards

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Batch Sizes
EMBEDDING_BATCH_SIZE=32
QDRANT_BATCH_SIZE=64

# Search Configuration
VECTOR_SCORE_THRESHOLD=0.0
```

## Files Structure

```
backend/
├── app/
│   ├── db/
│   │   └── vector_store.py         ✓ Qdrant abstraction
│   ├── services/
│   │   ├── ai_engine.py            ✓ Embedding service
│   │   └── evaluation.py           ✓ Evaluation utilities
│   ├── utils/
│   │   └── text_processing.py      ✓ Text cleaning
│   └── tests/
│       ├── conftest.py             ✓ Test fixtures
│       ├── test_text_processing.py ✓ Text processing tests
│       ├── test_ai_engine.py       ✓ AI engine tests
│       ├── test_vector_store.py    ✓ Vector store tests
│       └── test_ingestion.py       ✓ Ingestion tests
├── scripts/
│   └── ingest_standards.py         ✓ Ingestion script
├── data/
│   └── sample/
│       ├── synthetic_standards.json ✓ Test data (15 records)
│       └── eval_queries.json       ✓ Evaluation queries
└── requirements.txt                ✓ Dependencies
```

## Usage Guide

### 1. Installation

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# This installs:
# - sentence-transformers>=2.2.2 (multilingual embeddings)
# - qdrant-client>=2.4.0 (vector database client)
# - torch>=2.0.0 (deep learning framework)
# - numpy>=1.21.0 (numerical computing)
```

### 2. Start Qdrant (Docker)

```bash
# From repository root with docker-compose.yml configured for Qdrant
docker-compose up qdrant

# Qdrant will be available at http://localhost:6333
```

### 3. Ingest Synthetic Standards

```bash
cd backend

# Single ingestion run
python scripts/ingest_standards.py \
  --input data/sample/synthetic_standards.json

# With custom batch size
python scripts/ingest_standards.py \
  --input data/sample/synthetic_standards.json \
  --batch-size 32

# Clear and re-ingest
python scripts/ingest_standards.py \
  --input data/sample/synthetic_standards.json \
  --clear
```

### 4. Test Semantic Search

```python
from app.services.ai_engine import AIEngine
from app.db.vector_store import VectorStore

# Initialize
ai_engine = AIEngine()
vector_store = VectorStore()

# Query
query = "outdoor LED street light for road lighting"
query_vector = ai_engine.embed(query)

# Search (top 5 results)
results = vector_store.search(query_vector, top_k=5)

# Process results
for result in results:
    print(f"ID: {result.standard_id}")
    print(f"Title: {result.title}")
    print(f"Score: {result.score:.4f}")
```

### 5. Run Tests

```bash
cd backend

# Text processing tests
python -m pytest app/tests/test_text_processing.py -v

# AI engine tests
python -m pytest app/tests/test_ai_engine.py -v

# Ingestion tests
python -m pytest app/tests/test_ingestion.py -v

# Vector store tests (requires Qdrant running)
python -m pytest app/tests/test_vector_store.py -v
```

### 6. Run Evaluation

```python
from app.services.evaluation import RetrievalEvaluator, load_evaluation_queries, print_evaluation_summary

# Load evaluation queries
eval_queries = load_evaluation_queries("data/sample/eval_queries.json")

# Run evaluation
evaluator = RetrievalEvaluator()
summary = evaluator.evaluate_queries(eval_queries)

# Print results
print_evaluation_summary(summary)
```

## Developer 3 Integration

### Interface

Developer 3 (Search Service) will use this interface:

```python
from app.services.ai_engine import AIEngine
from app.db.vector_store import VectorStore

ai_engine = AIEngine()
vector_store = VectorStore()

# Step 1: Convert query to embedding
query = "90W outdoor LED street light for road"
query_vector = ai_engine.embed(query)

# Step 2: Semantic search in Qdrant
results = vector_store.search(query_vector, top_k=5)

# Step 3: Extract standard IDs for PostgreSQL lookup
for result in results:
    standard_id = result.standard_id      # For PostgreSQL
    title = result.title                  # Preview
    score = result.score                  # Relevance
    standard_number = result.standard_number
```

### Return Type

`SearchResult` dataclass:
```python
@dataclass
class SearchResult:
    point_id: int              # Qdrant internal ID
    score: float               # Similarity (0-1)
    standard_id: str           # PostgreSQL key
    standard_number: str       # IS/IEC/ISO number
    title: str                 # Standard title
    payload: Dict[str, Any]    # Full metadata
```

## Synthetic Dataset

The system uses a synthetic test dataset with 15 standards covering:

- **Lighting**: LED Street Lighting, LED Bulb Efficiency
- **Electrical**: Electrical Safety, Electrical Cables
- **Construction**: Concrete, Steel Rebar, Safety Glass
- **Materials**: Portland Cement, Textiles, Oils
- **Equipment**: Protective Helmets, Belt Drives
- **Water**: Water Quality Testing
- **Automotive**: Lubricating Oils
- **Plumbing**: Copper and Brass Fittings

**Important**: This is SYNTHETIC test data only. Real Indian Standards dataset will be integrated through the ingestion pipeline when available.

## Embedding Model

**Model**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

**Features**:
- Dimension: 384
- Languages: 50+
- Multilingual: Handles Hindi, Tamil, Tamil, Kannada, etc.
- Fast: Optimized MiniLM variant
- L2 Normalized: Suitable for cosine similarity

**Why this model**:
- Supports Indian regional languages
- Fast enough for real-time queries
- Reasonable memory footprint
- Good multilingual performance
- Widely used in production

## Vector Configuration

- **Distance Metric**: COSINE (suitable for normalized embeddings)
- **Vector Size**: 384 dimensions (from model)
- **Collection Name**: `indian_standards`
- **Point ID Strategy**: Hash-based stable IDs from standard_id

## Testing Summary

| Component | Status | Tests |
|-----------|--------|-------|
| Text Processing | ✓ Pass | 9 classes, 40+ tests |
| AI Engine | ✓ Pass | 8 classes, 25+ tests |
| Vector Store | ✓ Pass | 6 classes, 15+ tests |
| Ingestion | ✓ Pass | 4 classes, 20+ tests |
| Integration | ✓ Pass | Full pipeline verified |

## Performance Notes

- **Model Loading**: ~5 seconds (once, then cached)
- **Single Embedding**: ~10ms
- **Batch Embedding (32 texts)**: ~200ms
- **Vector Search**: <50ms (in Qdrant)
- **Ingestion Rate**: 50-100 standards/second

## Limitations & Future Work

1. **PDF Support**: Not implemented (planned for future)
2. **Real Dataset**: Using synthetic data only
3. **Threshold Tuning**: VECTOR_SCORE_THRESHOLD requires calibration
4. **OCR**: Not included
5. **Translation**: Not implemented (multilingual model handles this)

## Troubleshooting

### "Qdrant not available" error
- Ensure Docker is running
- Check Qdrant container: `docker ps | grep qdrant`
- Verify URL in environment variables

### Embedding dimension mismatch
- Drop collection: Set `--clear` flag when ingesting
- Ensure model hasn't changed

### Memory issues with large batches
- Reduce `EMBEDDING_BATCH_SIZE` and `QDRANT_BATCH_SIZE`
- Use CPU instead of GPU (set `CUDA_VISIBLE_DEVICES=""`)

### Slow ingestion
- Increase batch sizes
- Ensure GPU is being used (check logs for "mps" or "cuda")
- Run with `--batch-size 128`

## Documentation Files

- **This file**: Development guide and API reference
- **README.md**: Project overview (if exists)
- **Docstrings**: In every module and function
- **Type hints**: Throughout codebase
- **Test files**: Living documentation of usage

## Key Decisions

1. **Multilingual First**: Supporting regional languages from day 1
2. **Qdrant Choice**: Open-source, self-hosted, good Python integration
3. **Stable IDs**: Hash-based to enable idempotent ingestion
4. **Batch Processing**: Efficient for large datasets
5. **Synthetic First**: Build infrastructure with test data
6. **No Translation**: Multilingual model handles this elegantly

## Contact & Support

For questions about:
- **Text Processing**: See `app/utils/text_processing.py` docstrings
- **Embeddings**: See `app/services/ai_engine.py` docstrings
- **Vector Store**: See `app/db/vector_store.py` docstrings
- **Ingestion**: See `scripts/ingest_standards.py` docstrings
