# Simple Chatbot

A simplified Streamlit chatbot application that works with the simple_rag API for RAG (Retrieval-Augmented Generation) queries.

## Features

- **Conversation Management**: Create, list, and delete conversations
- **Chat Interface**: Interactive chat with message history
- **Source Display**: Show sources from RAG queries (filename and chunk information)
- **Auto-Title Generation**: Automatically generates conversation titles using OpenAI

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database (shared with simple_rag)
- simple_rag API running
- OpenAI API key (for title generation)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment variables:
```bash
cp .env.example .env
```

3. Configure your `.env` file:
   - `RAG_API_BASE_URL`: URL of the simple_rag API (default: http://localhost:8000)
   - `RDS_*`: PostgreSQL database credentials (same as simple_rag)
   - `OPENAI_API_KEY`: OpenAI API key for generating conversation titles

4. Run the application:
```bash
streamlit run src/main.py
```

## Configuration

The application uses environment variables for configuration:

- **RAG_API_BASE_URL**: Base URL for the simple_rag API
- **RDS_HOST, RDS_DB, RDS_USER, RDS_PASSWORD, RDS_PORT**: PostgreSQL connection settings
- **OPENAI_API_KEY**: OpenAI API key for conversation title generation

## Usage

1. Start a new conversation by typing a question in the chat input
2. View conversation history in the sidebar
3. Click on any conversation in the sidebar to load its history
4. Delete conversations using the trash icon in the sidebar
5. View sources for assistant responses below each message

## Project Structure

```
simple_chatbot/
├── src/
│   ├── main.py                   # Main Streamlit application
│   ├── conversation_manager.py   # Conversation management with SQLAlchemy
│   ├── settings.py                # Application settings
│   ├── chat_manager.py           # Compatibility layer (unused)
│   └── utils.py                   # Utility functions
├── requirements.txt
├── .env.example
└── README.md
```

## Integration with simple_rag

This chatbot connects to the simple_rag API's `/ask` endpoint:

**Request Format:**
```json
{
  "query": "Your question here",
  "top_k": 5,
  "use_reranking": true
}
```

**Response Format:**
```json
{
  "query": "Your question here",
  "response": "AI-generated response",
  "sources": [
    {
      "chunk_id": "document_chunk_0",
      "filename": "path/to/document.md",
      "chunk_text": "Source content...",
      "document_id": "document"
    }
  ]
}
```

## Database Schema

The chatbot uses the same database schema as simple_rag:
- `conversations` table: Stores conversation metadata
- `messages` table: Stores user and assistant messages with sources

## License

MIT

