# RAG API with PostgreSQL + pgvector (Semantic Search)

This is the **new implementation** of the RAG API using PostgreSQL with pgvector for pure semantic vector search.

## Key Improvements

- ✅ **Single Database**: All data in PostgreSQL (no Milvus dependency)
- ✅ **Cost Savings**: ~$10-50/month savings
- ✅ **Pure Semantic Search**: Clean cosine similarity matching
- ✅ **Pure SQLAlchemy**: No raw SQL queries
- ✅ **Simplified API**: Clean and straightforward vector search
- ✅ **Fast & Efficient**: Direct vector similarity with optional indexing

## Architecture

### Semantic Search

The vector database uses pure semantic search with OpenAI embeddings:

```python
# Simple cosine similarity search
results = await vector_db.search(query="query", top_k=5)
```

- **Vector Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
- **Similarity**: Cosine distance/similarity
- **Search**: Direct k-nearest neighbors

### API

**Simple and clean:**
```python
results = await vector_db.search(
    query="How to use FastAPI?",
    top_k=5  # Number of results
)

# Returns list of dicts with:
# - id, document_id, chunk_id, filename, chunk_text
# - distance (0-2, lower = more similar)
# - similarity (0-1, higher = more similar)
```

## Setup

### 1. Prerequisites

- PostgreSQL 12+ with pgvector extension
- Python 3.8+
- OpenAI API key

### 2. Enable pgvector

Run the setup SQL file on your PostgreSQL database:

```bash
psql -U your_user -d your_database -f setup_pgvector.sql
```

Or manually:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create `.env` file:

```env
OPENAI_API_KEY=sk-...
RDS_USER=your_user
RDS_PASSWORD=your_password
RDS_HOST=localhost
RDS_DB=your_database
RDS_PORT=5432
```

### 5. Run the Application

```bash
# Initialize tables and start server
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The application will:
1. Create database tables (including `document_chunks`)
2. The trigger will auto-populate `text_search_vector` column
3. Start the FastAPI server

### 6. Ingest Documents

```bash
# If you have an ingestion script
python ingest_documents.py
```

## Usage

### Basic Query

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to use FastAPI?",
    "top_k": 5,
    "use_reranking": false
  }'
```

### Query with Reranking

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to use FastAPI?",
    "top_k": 5,
    "use_reranking": true
  }'
```

This will retrieve 15 documents (5 * 3), rerank them, and return top 5.

## File Structure

```
rag_pg/
├── README.md                    # This file
├── setup_pgvector.sql          # Database setup script
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
└── src/
    ├── main.py                 # FastAPI application
    ├── models/
    │   ├── db.py              # SQLAlchemy models (with DocumentChunk)
    │   └── api.py             # Pydantic models
    ├── utils/
    │   ├── vector_db.py       # Semantic vector database
    │   ├── database_client.py # PostgreSQL client
    │   └── text_chunker.py    # Document chunking
    ├── services/
    │   ├── rag_service.py     # RAG logic (updated)
    │   └── conversation_service.py
    ├── core/
    │   ├── config.py          # Settings (no Milvus)
    │   └── dependencies.py    # Dependency injection
    ├── api/
    │   └── endpoints/         # API routes
    └── docs/                  # Documentation
```

## Database Schema

### document_chunks Table

```sql
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id VARCHAR(256) NOT NULL,
    chunk_id VARCHAR(256) NOT NULL,
    filename VARCHAR(256) NOT NULL,
    chunk_text TEXT NOT NULL,
    dense_vector VECTOR(3072),  -- OpenAI embedding
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(document_id, chunk_id)
);
```

## Performance

### Small Dataset (<10K docs)
- Query time: 100-300ms
- No special indexes needed

### Medium Dataset (10K-100K docs)
- Query time: 200-500ms
- Recommended: Add IVFFlat vector index

```sql
CREATE INDEX idx_vector ON document_chunks 
USING ivfflat (dense_vector vector_cosine_ops)
WITH (lists = 100);
```

## Migration from Old Implementation

The old `rag/` directory uses Milvus. This `rag_pg/` is the new implementation. Both can coexist during testing.

To switch:
1. Test `rag_pg/` locally
2. Update Dockerfile to use `rag_pg/`
3. Update deployment scripts
4. Deploy to production
5. Remove old `rag/` when confident

## Troubleshooting

### "relation document_chunks does not exist"
→ Run the application first to create tables

### "extension vector does not exist"
→ Enable pgvector extension: `CREATE EXTENSION vector;`

### Slow queries
→ Add vector index (see Performance section)

### Poor search results
→ Verify your OpenAI embeddings are being generated correctly
→ Check the `similarity` scores in results - should be >0.5 for relevant matches

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Run Tests

```bash
pytest tests/
```

### Check Linting

```bash
ruff check src/
```

### Format Code

```bash
ruff format src/
```

## Next Steps

1. ✅ Local testing
2. ✅ Update Terraform for pgvector
3. ✅ Deploy to staging
4. ✅ Ingest documents
5. ✅ Performance testing
6. ✅ Deploy to production

## Support

For questions or issues, refer to:
- PostgreSQL pgvector docs: https://github.com/pgvector/pgvector
- FastAPI docs: https://fastapi.tiangolo.com/
- OpenAI docs: https://platform.openai.com/docs

