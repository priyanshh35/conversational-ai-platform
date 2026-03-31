# Conversational AI Platform

A production-ready FastAPI application that powers context-aware, personalized conversational AI with Retrieval Augmented Generation (RAG), conversation state management, and analytics.

---

## Features

- **Multi-turn conversation management** with sliding window context and automatic summarization
- **RAG pipeline** using vector search (ChromaDB) + neural reranking (usf-rerank)
- **User profiling and personalization** — tone, verbosity, and expertise-level adaptation
- **Conversation repair detection** — automatically detects and handles user corrections
- **Sentiment scoring** per message turn
- **Analytics endpoints** — per-conversation and global platform metrics
- **Tech Support knowledge base** — 17 seeded documents across 3 categories

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| LLM | usf1-mini (OpenAI-compatible) |
| Embeddings | usf-embed |
| Reranker | usf-rerank |
| Vector Database | ChromaDB |
| Relational Database | SQLite + SQLAlchemy |
| Validation | Pydantic v2 |
| Server | Uvicorn |

---

## Project Structure
```
conversational-ai-platform/
├── app/
│   ├── main.py              # FastAPI app + all route definitions
│   ├── config.py            # Environment variable management
│   ├── database.py          # SQLAlchemy engine + session management
│   ├── models.py            # Database table definitions (User, Conversation, Message)
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── llm.py               # LLM, embedding, and reranker API calls
│   ├── rag.py               # ChromaDB vector store + retrieval pipeline
│   ├── conversation.py      # History management, repair detection, sentiment
│   ├── personalization.py   # User profile → system prompt builder
│   └── analytics.py        # Metrics computation
├── docs/
│   ├── api_documentation.md
│   ├── rag_architecture.md
│   └── design_decisions.md
├── seed_knowledge_base.py   # One-time KB population script
├── requirements.txt
├── .env.example
└── README.md
```

---

## Installation

### Prerequisites
- Python 3.10+
- pip
- Git

### 1. Clone the repository
```bash
git clone https://github.com/priyanshh35/conversational-ai-platform.git
cd conversational-ai-platform
```

### 2. Create and activate virtual environment
```bash
# Mac/Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:
```env
API_KEY=your_api_key_here

CHAT_BASE_URL=https://api.us.inc/usf/v1/hiring
EMBED_BASE_URL=https://api.us.inc/usf/v1/hiring/embed
RERANK_BASE_URL=https://api.us.inc/usf/v1/hiring/embed

MODEL_NAME=usf1-mini
EMBEDDING_MODEL=usf-embed
RERANK_MODEL=usf-rerank

DATABASE_URL=sqlite:///./conversations.db
CHROMA_DB_PATH=./chroma_db
MAX_HISTORY_TURNS=10
```

### 5. Seed the knowledge base
```bash
python seed_knowledge_base.py
```

Expected output:
```
Seeding knowledge base...
Adding 17 documents...
Done! Knowledge base now has 17 documents.
```

### 6. Start the server
```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Open Swagger UI
Navigate to: **http://localhost:8000/docs**

---

## Quick Start — End to End Test

### Create a user
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "profile": {
      "tone": "casual",
      "verbosity": "medium",
      "expertise_level": "beginner"
    }
  }'
```

### Start a conversation
```bash
curl -X POST http://localhost:8000/conversations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "<user_id>", "title": "Password Help"}'
```

### Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "<conversation_id>",
    "user_id": "<user_id>",
    "message": "How do I reset my password?"
  }'
```

### Check analytics
```bash
curl http://localhost:8000/analytics/global
```

---

## API Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/users` | Create user with profile |
| GET | `/users/{id}` | Get user details |
| PATCH | `/users/{id}/profile` | Update personalization profile |
| POST | `/conversations` | Start new conversation |
| GET | `/conversations/{id}` | Get conversation details |
| GET | `/users/{id}/conversations` | List all user conversations |
| GET | `/conversations/{id}/messages` | Get full message history |
| DELETE | `/conversations/{id}` | Archive conversation |
| POST | `/chat` | Send message and get AI response |
| GET | `/analytics/conversation/{id}` | Per-conversation metrics |
| GET | `/analytics/global` | Platform-wide metrics |

---

## Knowledge Base Categories

| Category | Documents | Description |
|---|---|---|
| Tech Support | 10 docs | Password reset, crashes, network, billing, API, 2FA, webhooks |
| Repair Patterns | 3 docs | Misunderstanding, frustration, repetition handling |
| Style Templates | 4 docs | Formal, casual, expert, beginner response styles |

---

## Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `API_KEY` | Provider API key | `sk-...` |
| `CHAT_BASE_URL` | Chat completions base URL | `https://api.us.inc/usf/v1/hiring` |
| `EMBED_BASE_URL` | Embeddings base URL | `https://api.us.inc/usf/v1/hiring/embed` |
| `RERANK_BASE_URL` | Reranker base URL | `https://api.us.inc/usf/v1/hiring/embed` |
| `MODEL_NAME` | LLM model name | `usf1-mini` |
| `EMBEDDING_MODEL` | Embedding model name | `usf-embed` |
| `RERANK_MODEL` | Reranker model name | `usf-rerank` |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./conversations.db` |
| `CHROMA_DB_PATH` | ChromaDB persistence path | `./chroma_db` |
| `MAX_HISTORY_TURNS` | Sliding window size | `10` |