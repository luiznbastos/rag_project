"""
RAG Service for handling document queries with hybrid search and reranking.
"""
import logging
import asyncio
import json
from typing import List, Dict, Any
from openai import OpenAI

try:
    from src.models.api import QueryRequest, QueryResponse
    from src.utils.vector_db import VectorDatabase
except ImportError:
    from models.api import QueryRequest, QueryResponse
    from utils.vector_db import VectorDatabase

logger = logging.getLogger(__name__)


class RagService:
    """Service for handling RAG operations."""
    
    def __init__(self, vector_database: VectorDatabase, openai_client: OpenAI):
        self.vector_database = vector_database
        self.openai_client = openai_client
    
    async def _rerank_documents_with_openai(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Reranks documents using an LLM for semantic relevance."""
        if not self.openai_client or not documents:
            return documents

        async def score_document(doc: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
            prompt = f"""
            Given the user query, evaluate the following document's relevance. 
            Provide a score from 0.0 (not relevant) to 1.0 (highly relevant) and a brief reasoning.

            Query: "{query}"

            Document: "{doc.get('chunk_text', '')}"
            """
            try:
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model="gpt-5-nano",
                    messages=[
                        {"role": "system", "content": "You are a relevance scoring expert. Respond with a JSON object containing 'relevance_score' (float between 0.0 and 1.0) and 'reasoning' (string)."},
                        {"role": "user", "content": prompt}
                    ],
                )
                
                response_text = response.choices[0].message.content
                try:
                    if '{' in response_text and '}' in response_text:
                        start = response_text.find('{')
                        end = response_text.rfind('}') + 1
                        json_str = response_text[start:end]
                        parsed = json.loads(json_str)
                        relevance_score = float(parsed.get('relevance_score', 0.0))
                        return (relevance_score, doc)
                    else:
                        return (0.0, doc)
                except (json.JSONDecodeError, ValueError, KeyError):
                    return (0.0, doc)
            except Exception as e:
                logger.error(f"Error reranking document: {e}")
                return (0.0, doc)

        scoring_tasks = [score_document(doc) for doc in documents]
        scored_docs = await asyncio.gather(*scoring_tasks)
        
        reranked_docs = sorted(scored_docs, key=lambda x: x[0], reverse=True)
        
        return [doc for score, doc in reranked_docs]
    
    async def _generate_rag_response(
        self,
        query: str,
        context_docs: List[Dict[str, Any]]
    ) -> str:
        """Generates a final response using the retrieved and reranked context."""
        if not self.openai_client:
            return "Error: OpenAI client not configured."

        context = ""
        for doc in context_docs:
            filename = doc.get('filename', 'N/A')
            chunk_id = doc.get('chunk_id', 'N/A')
            context += f"Source: {filename} - Chunk {chunk_id}\n"
            context += f"Content: {doc.get('chunk_text', '')}\n\n"

        prompt = f"""
        You are an expert Q&A assistant. Use the following context to answer the user's question.
        If the context does not contain the answer, state that you could not find the information.

        Context:
        ---
        {context}
        ---

        Question: "{query}"
        """
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a helpful Q&A assistant."},
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return "An error occurred while generating the response."
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Main business logic for processing document queries."""
        
        # Step 1: Initial retrieval with Semantic Search
        # Retrieve more documents initially to give the reranker more to work with
        retrieval_limit = request.top_k * 3 if request.use_reranking else request.top_k
        similar_docs = await self.vector_database.search(
            query=request.query,
            top_k=retrieval_limit
        )

        # Step 2: AI-powered Reranking
        if request.use_reranking and similar_docs:
            logger.info(f"Reranking {len(similar_docs)} documents...")
            final_docs = await self._rerank_documents_with_openai(request.query, similar_docs)
            final_docs = final_docs[:request.top_k]
        else:
            final_docs = similar_docs[:request.top_k]

        # Step 3: Generate final response
        if final_docs:
            logger.info(f"Generating response using {len(final_docs)} documents")
            response_text = await self._generate_rag_response(request.query, final_docs)
        else:
            response_text = "I couldn't find any relevant information to answer your question."

        return QueryResponse(
            query=request.query,
            response=response_text,
            sources=final_docs
        )

