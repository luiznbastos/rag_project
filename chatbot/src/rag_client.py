import logging
import requests
from typing import List, Dict, Any, Optional, Tuple

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

from settings import settings

logger = logging.getLogger(__name__)


class RAGClient:
    """Client for interacting with the RAG API."""
    
    def __init__(self, base_url: str = None, openai_api_key: str = None):
        """Initialize the RAG client."""
        self.base_url = (base_url or settings.rag_api_base_url).rstrip('/')
        self.timeout = 60
        
        self.openai_client = None
        if OPENAI_AVAILABLE and (openai_api_key or settings.openai_api_key):
            try:
                self.openai_client = OpenAI(api_key=openai_api_key or settings.openai_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    def ask(self, query: str, top_k: int = 5, use_reranking: bool = True) -> Tuple[str, List[Dict]]:
        """
        Send a query to the RAG API and get a response.
        
        Returns:
            Tuple of (answer_text, sources)
        """
        try:
            response = requests.post(
                f"{self.base_url}/ask",
                json={
                    "query": query,
                    "top_k": top_k,
                    "use_reranking": use_reranking,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            answer_text = data.get("response") or data.get("answer") or ""
            sources = data.get("sources", [])
            return answer_text, sources
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to RAG API: {e}")
            raise
    
    def create_conversation(self, title: str) -> str:
        """
        Create a new conversation.
        
        Returns:
            conversation_id
        """
        try:
            response = requests.post(
                f"{self.base_url}/conversations",
                json={"title": title},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            conversation_id = data.get("conversation_id")
            logger.info(f"Created conversation '{title}' (ID: {conversation_id[:8]}...)")
            return conversation_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of conversations.
        
        Returns:
            List of conversation dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/conversations",
                params={"limit": limit},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            conversations = data.get("conversations", [])
            return conversations
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing conversations: {e}")
            return []
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific conversation.
        
        Returns:
            Conversation dictionary or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/conversations/{conversation_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Conversation {conversation_id} not found")
                return None
            logger.error(f"Error getting conversation: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting conversation: {e}")
            raise
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.delete(
                f"{self.base_url}/conversations/{conversation_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info(f"Deleted conversation {conversation_id[:8]}...")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Conversation {conversation_id} not found")
                return False
            logger.error(f"Error deleting conversation: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting conversation: {e}")
            raise
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages for a conversation.
        
        Returns:
            List of message dictionaries
        """
        try:
            response = requests.get(
                f"{self.base_url}/conversations/{conversation_id}/messages",
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            messages = data.get("messages", [])
            return messages
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str, 
        sources: Optional[List[Dict]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Add a message to a conversation.
        
        Returns:
            Message dictionary or None if failed
        """
        try:
            response = requests.post(
                f"{self.base_url}/conversations/{conversation_id}/messages",
                json={
                    "role": role,
                    "content": content,
                    "sources": sources,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info(f"Added {role} message to conversation {conversation_id[:8]}...")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    def generate_conversation_title(self, first_query: str) -> str:
        """Generate a concise title from the first user query using OpenAI."""
        if not self.openai_client or not OPENAI_AVAILABLE:
            return first_query[:50] + "..." if len(first_query) > 50 else first_query
        
        try:
            prompt = f'''Extract a short, concise title (max 5 words) that summarizes this question:
            "{first_query}"
            
            Return only the title, nothing else.'''
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise titles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=20
            )
            
            title = response.choices[0].message.content.strip()
            if len(title) > 100:
                title = title[:100] + "..."
            
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return first_query[:50] + "..." if len(first_query) > 50 else first_query


# Global RAG client instance
_rag_client = None

def get_rag_client() -> RAGClient:
    """Get RAG client with lazy initialization."""
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient()
    return _rag_client

