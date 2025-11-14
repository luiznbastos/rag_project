# Project Restructuring Summary

**Date:** November 2, 2025  
**Status:** ✅ Complete

## What Was Done

### 1. Ignore Legacy Folder

**Created `.gitignore`:**
- Added Python, IDE, environment, testing, and OS ignores
- Added `legacy/` to ignore list
- Added Terraform state files

**Created `.dockerignore`:**
- Added build artifacts, tests, docs to ignore
- Added `legacy/` to Docker ignore
- Optimized Docker build context

### 2. Directory Restructuring

**Renamed:**
```bash
rag_pg/ → rag/
```

The new `rag/` directory is now the main RAG API implementation with:
- Pure semantic search (no hybrid/text search)
- PostgreSQL + pgvector
- Simplified codebase

### 3. Docker Configuration

**Created `rag/Dockerfile`:**
```dockerfile
FROM python:3.11-slim
- System dependencies: gcc, postgresql-client, curl
- Layer caching with requirements.txt first
- Health check on /health endpoint
- Runs on port 8000 with uvicorn
```

**Created `rag/.dockerignore`:**
- Excludes unnecessary files from Docker build
- Reduces image size
- Speeds up builds

**Created `rag/env.example`:**
- Template for environment variables
- OpenAI API key configuration
- PostgreSQL connection settings
- Logging and chunking config

### 4. Updated docker-compose.yml

**Added local PostgreSQL service:**
```yaml
postgres:
  image: ankane/pgvector:latest
  - Auto-runs setup_pgvector.sql on init
  - Persistent volume for data
  - Health checks
```

**Updated rag-api service:**
```yaml
rag-api:
  build:
    context: ./rag  # Updated from rag_pg
  depends_on:
    postgres: service_healthy
  - Added build configuration
  - Defaults to local postgres
  - Added LOG_LEVEL environment var
```

**Key Features:**
- Local PostgreSQL with pgvector for development
- Automatic setup with SQL init script
- Health checks on all services
- Service dependencies properly configured
- Persistent data volume

### 5. Verified Existing Configuration

**Makefile:** ✅ Already correct
- Builds from `./rag` directory
- ECR tagging and pushing configured
- Complete deployment workflow

**Terraform:** ✅ Already correct
- No `rag_pg` references found
- user_data.sh uses correct paths
- pgvector parameter group already configured
- Milvus references already removed

## New Project Structure

```
rag_project/
├── .gitignore                    # NEW: Ignores legacy/
├── .dockerignore                 # NEW: Ignores legacy/
├── docker-compose.yml            # UPDATED: Local postgres + build config
├── Makefile                      # ✓ Already correct
├── RESTRUCTURE_SUMMARY.md        # NEW: This file
├── rag/                          # RENAMED from rag_pg/
│   ├── Dockerfile                # NEW: Production-ready build
│   ├── .dockerignore             # NEW: Optimized build context
│   ├── env.example               # NEW: Environment template
│   ├── requirements.txt          # pgvector, no Milvus
│   ├── setup_pgvector.sql        # Simplified (no triggers)
│   ├── README.md                 # Semantic search docs
│   └── src/
│       ├── main.py
│       ├── models/
│       │   └── db.py             # DocumentChunk (no text_search_vector)
│       ├── utils/
│       │   └── vector_db.py      # Pure semantic search
│       ├── services/
│       │   └── rag_service.py    # Simplified, no hybrid
│       └── ...
├── chatbot/                      # Streamlit UI
├── terraform/                    # AWS infrastructure
└── legacy/                       # OLD: Milvus + hybrid implementation
    └── rag/                      # (Ignored by Git/Docker)
```

## Benefits

### Simplicity
- ✅ **Single directory** for main implementation
- ✅ **No confusion** between old and new code
- ✅ **Legacy preserved** but ignored
- ✅ **Clean structure** with proper ignores

### Development
- ✅ **Local PostgreSQL** with pgvector for testing
- ✅ **One command** to start everything: `docker-compose up`
- ✅ **Auto-setup** with SQL init script
- ✅ **Proper health checks** and dependencies

### Deployment
- ✅ **Production-ready** Dockerfile
- ✅ **Layer caching** for faster builds
- ✅ **Optimized** Docker context
- ✅ **Makefile** for CI/CD automation

## How to Use

### Local Development

```bash
# 1. Copy environment template
cp rag/env.example .env
# Edit .env with your OpenAI API key

# 2. Start all services (postgres + rag-api + chatbot)
docker-compose up -d

# 3. Check health
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health

# 4. View logs
docker-compose logs -f rag-api

# 5. Connect to PostgreSQL
docker exec -it postgres-pgvector psql -U postgres -d rag_db

# 6. Stop services
docker-compose down
```

### Production Deployment

```bash
# 1. Build and push to ECR
make deploy

# 2. Deploy infrastructure (if not already done)
cd terraform && terraform apply

# 3. Deploy to EC2 (via GitHub Actions or manually)
# GitHub Actions will automatically deploy on push to main
```

### Testing Docker Build

```bash
# Build RAG API
docker build -t rag-api:latest ./rag

# Run locally
docker run -p 8000:8000 --env-file .env rag-api:latest

# Test endpoint
curl http://localhost:8000/health
```

## docker-compose.yml Key Features

### Development Mode (Default)
- Uses local PostgreSQL with pgvector
- Builds images locally from source
- Data persists in named volume
- Auto-runs setup_pgvector.sql

### Production Mode
- Comment out `postgres` service
- Use ECR images instead of building
- Connect to AWS RDS
- Set `RDS_HOST` to RDS endpoint

## Environment Variables

### Required
```env
OPENAI_API_KEY=sk-...          # OpenAI API key
```

### PostgreSQL (with defaults for local dev)
```env
RDS_HOST=postgres              # Default: local postgres container
RDS_PORT=5432                  # Default: 5432
RDS_DB=rag_db                  # Default: rag_db
RDS_USER=postgres              # Default: postgres
RDS_PASSWORD=password          # Default: password (change for prod!)
```

### Optional
```env
LOG_LEVEL=INFO                 # Default: INFO
CHUNK_SIZE=2000                # Default: 2000
CHUNK_OVERLAP=200              # Default: 200
IMAGE_TAG=latest               # Default: latest
```

## Changes from Previous Structure

| Aspect | Before | After |
|--------|--------|-------|
| **Directory** | `rag_pg/` | `rag/` |
| **Search** | Hybrid (vector + text) | Pure semantic |
| **Docker** | No Dockerfile | Production-ready Dockerfile |
| **Local DB** | None | PostgreSQL with pgvector |
| **docker-compose** | Images only | Build + local postgres |
| **Collection** | Had collection abstraction | Removed |
| **Complexity** | High | Low |

## Next Steps

### For Local Testing
1. [ ] Start docker-compose: `docker-compose up -d`
2. [ ] Verify postgres has pgvector: `SELECT * FROM pg_extension;`
3. [ ] Ingest test documents
4. [ ] Test search endpoint
5. [ ] Test chatbot UI

### For Production
1. [ ] Update .env with production RDS endpoint
2. [ ] Enable pgvector on RDS: `CREATE EXTENSION vector;`
3. [ ] Run setup_pgvector.sql on RDS
4. [ ] Build and push images: `make deploy`
5. [ ] Deploy to EC2 via GitHub Actions
6. [ ] Ingest production documents
7. [ ] Verify semantic search working

## Verification Commands

```bash
# Check structure
ls -la rag/

# Verify Docker files
ls -la rag/Dockerfile rag/.dockerignore

# Check docker-compose syntax
docker-compose config

# Test build
docker build -t rag-api:test ./rag

# Start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs rag-api
docker-compose logs postgres

# Check PostgreSQL
docker exec -it postgres-pgvector psql -U postgres -d rag_db -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Stop everything
docker-compose down -v  # -v removes volumes
```

## Troubleshooting

### "Cannot find rag directory"
→ Make sure you renamed `rag_pg` to `rag`: `mv rag_pg rag`

### "postgres: port 5432 already in use"
→ Stop local PostgreSQL: `sudo systemctl stop postgresql`
→ Or change port in docker-compose.yml

### "setup_pgvector.sql not found"
→ Make sure `rag/setup_pgvector.sql` exists
→ Check docker-compose volume mapping

### "Health check failing"
→ Wait longer (start_period: 40s)
→ Check logs: `docker-compose logs rag-api`
→ Verify database connection

## Success Criteria

All complete:
- ✅ `rag_pg/` renamed to `rag/`
- ✅ `.gitignore` ignores `legacy/`
- ✅ `.dockerignore` created
- ✅ `rag/Dockerfile` created
- ✅ `rag/.dockerignore` created
- ✅ `rag/env.example` created
- ✅ `docker-compose.yml` updated with postgres
- ✅ Makefile verified (already correct)
- ✅ Terraform verified (already correct)

Ready for testing:
- ⏳ Local docker-compose test
- ⏳ Docker build verification
- ⏳ PostgreSQL + pgvector verification
- ⏳ API endpoint testing
- ⏳ Production deployment

---

**Result:** The project is now properly structured with a clean separation between the new simplified implementation (`rag/`) and the legacy hybrid implementation (`legacy/`). The Docker configuration enables easy local development and smooth production deployment.

