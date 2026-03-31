# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
All requests are unauthenticated at the API level (auth is handled at the provider level via `x-api-key` in the server's outbound calls).

---

## Health

### GET `/health`
Returns server status.

**Response**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

---

## Users

### POST `/users`
Create a new user with a personalization profile.

**Request Body**
```json
{
  "username": "alice",
  "email": "alice@example.com",
  "profile": {
    "tone": "casual",
    "verbosity": "medium",
    "expertise_level": "beginner",
    "topics_of_interest": ["password", "billing"]
  }
}
```

**Profile Fields**
| Field | Options | Default |
|---|---|---|
| `tone` | `formal`, `casual`, `neutral` | `neutral` |
| `verbosity` | `brief`, `medium`, `detailed` | `medium` |
| `expertise_level` | `beginner`, `intermediate`, `expert` | `intermediate` |
| `topics_of_interest` | any list of strings | `[]` |

**Response `201`**
```json
{
  "id": "uuid",
  "username": "alice",
  "email": "alice@example.com",
  "profile": { ... },
  "created_at": "2024-01-01T00:00:00"
}
```

---

### GET `/users/{user_id}`
Fetch user details and current profile.

**Response `200`** — same as UserOut schema above.

**Response `404`**
```json
{ "detail": "User not found" }
```

---

### PATCH `/users/{user_id}/profile`
Partially update a user's personalization profile. Only send fields you want to change.

**Request Body**
```json
{
  "profile": {
    "tone": "formal",
    "expertise_level": "expert"
  }
}
```

**Response `200`** — updated UserOut object.

---

## Conversations

### POST `/conversations`
Start a new conversation session for a user.

**Request Body**
```json
{
  "user_id": "uuid",
  "title": "Password Reset Help"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Password Reset Help",
  "total_turns": 0,
  "summary": null,
  "created_at": "...",
  "updated_at": "..."
}
```

---

### GET `/conversations/{conversation_id}`
Get conversation metadata including turn count and summary.

---

### GET `/users/{user_id}/conversations`
List all conversations for a user.

**Response `200`** — array of ConversationOut objects.

---

### GET `/conversations/{conversation_id}/messages`
Get the full message history for a conversation with all quality metadata.

**Response `200`**
```json
[
  {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "user",
    "content": "How do I reset my password?",
    "created_at": "...",
    "rag_hit": false,
    "response_latency": null,
    "sentiment_score": 0.0,
    "is_repair_turn": false
  },
  {
    "id": "uuid",
    "conversation_id": "uuid",
    "role": "assistant",
    "content": "No problem! Here are the steps...",
    "created_at": "...",
    "rag_hit": true,
    "response_latency": 15.78,
    "sentiment_score": 0.5,
    "is_repair_turn": false
  }
]
```

---

### DELETE `/conversations/{conversation_id}`
Soft-archive a conversation (sets `is_active=false`). Data is retained.

**Response `200`**
```json
{ "message": "Conversation archived" }
```

---

## Chat

### POST `/chat`
The core endpoint. Sends a user message and returns a personalized, RAG-augmented AI response.

**Request Body**
```json
{
  "conversation_id": "uuid",
  "user_id": "uuid",
  "message": "I forgot my password and can't log in."
}
```

**Response `200`**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "response": "No problem — easy fix. Follow these steps...",
  "rag_hit": true,
  "rag_sources": ["account", "account", "account"],
  "latency_seconds": 15.78,
  "repair_detected": false
}
```

**Response Fields**
| Field | Description |
|---|---|
| `response` | The AI generated reply |
| `rag_hit` | Whether ChromaDB found relevant context |
| `rag_sources` | KB categories used (e.g. account, billing, repair) |
| `latency_seconds` | End-to-end LLM response time |
| `repair_detected` | Whether the message was a correction/repair turn |

**Internal Processing Order**
1. Validate conversation + user
2. Detect repair intent
3. Compute user message sentiment
4. RAG: embed query → ChromaDB retrieval → rerank
5. Build personalized system prompt with RAG context
6. Load conversation history (sliding window)
7. Call LLM
8. Persist both messages with metadata
9. Update conversation stats

---

## Analytics

### GET `/analytics/conversation/{conversation_id}`
Quality metrics for a single conversation.

**Response `200`**
```json
{
  "conversation_id": "uuid",
  "total_turns": 5,
  "avg_latency": 18.72,
  "rag_hit_rate": 1.0,
  "repair_rate": 0.1,
  "avg_sentiment": 0.3
}
```

**Metrics Explained**
| Metric | Description |
|---|---|
| `total_turns` | Number of assistant replies |
| `avg_latency` | Mean LLM response time in seconds |
| `rag_hit_rate` | Fraction of turns where RAG retrieved context |
| `repair_rate` | Fraction of messages flagged as repair turns |
| `avg_sentiment` | Mean sentiment score (-1.0 angry → +1.0 happy) |

---

### GET `/analytics/global`
Aggregated metrics across the entire platform.

**Response `200`**
```json
{
  "total_users": 2,
  "total_conversations": 2,
  "total_messages": 12,
  "avg_latency": 18.72,
  "rag_hit_rate": 1.0,
  "repair_rate": 0.1,
  "avg_sentiment": 0.3,
  "avg_session_length": 5.0
}
```

**Additional Fields**
| Field | Description |
|---|---|
| `total_users` | Registered users |
| `total_conversations` | Total sessions started |
| `total_messages` | All messages across all conversations |
| `avg_session_length` | Average turns per conversation |