-- PostgreSQL setup for pgvector
-- Run this SQL file once on your PostgreSQL database

-- Step 1: Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2 (Optional): Create indexes for better performance
-- Vector index (IVFFlat - good for small to medium datasets)
-- Uncomment after you have data ingested (requires at least 1000 rows)
-- CREATE INDEX IF NOT EXISTS idx_vector ON document_chunks 
-- USING ivfflat (dense_vector vector_cosine_ops)
-- WITH (lists = 100);

-- Regular index on document_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_document_id ON document_chunks (document_id);

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'pgvector setup complete! You can now:';
    RAISE NOTICE '1. Run your application to create tables';
    RAISE NOTICE '2. Ingest documents';
    RAISE NOTICE '3. Optionally create vector index after ingestion (if > 1000 docs)';
END $$;
