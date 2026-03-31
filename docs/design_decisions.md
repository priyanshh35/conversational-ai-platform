# Design Decisions & Trade-offs

## Architecture Decisions

### 1. FastAPI over Flask or Django
**Decision:** FastAPI
**Reason:** Native async support, automatic Swagger UI generation from type
hints, Pydantic v2 validation built in, and significantly better performance
for I/O-bound workloads like LLM API calls.
**Trade-off:** Smaller ecosystem than Django; no built-in admin panel.

---

### 2. SQLite over PostgreSQL
**Decision:** SQLite with SQLAlchemy ORM
**Reason:** Zero setup — runs with a single file, no server process needed.
Perfect for a demo/assessment where the evaluator needs to run the project
with one command.
**Trade-off:** Not suitable for concurrent writes in production. Switching to
PostgreSQL requires only changing the `DATABASE_URL` env variable — the
SQLAlchemy ORM abstracts the difference entirely.

---

### 3. ChromaDB over Pinecone / Weaviate
**Decision:** ChromaDB (local persistent)
**Reason:** Runs entirely locally with no account, API key, or network
dependency. Persists to disk automatically. Cosine similarity index is
production-quality for moderate document counts.
**Trade-off:** Not horizontally scalable. For production with millions of
documents, Pinecone or Weaviate would be the right choice. ChromaDB itself
offers a cloud-hosted version as a migration path.

---

### 4. Two-stage RAG (retrieve + rerank) over single-stage
**Decision:** ChromaDB retrieval → usf-rerank neural reranker
**Reason:** Vector similarity alone is imprecise — it measures geometric
distance between embeddings, not true semantic relevance. The reranker
understands the query-document relationship and significantly improves
precision. Proven in testing: repair pattern chunks were correctly promoted
over account docs when the user said "you misunderstood me."
**Trade-off:** Adds one extra API call per turn (~2-3s latency). Worth it
for quality; could be made optional for latency-sensitive applications.

---

### 5. Sliding window + summarization over full history
**Decision:** Keep last 10 turns verbatim, summarize older turns
**Reason:** Balances two competing needs — the LLM needs enough context to
be coherent, but sending the full history of a long conversation wastes
tokens and eventually exceeds the context window.
**Trade-off:** The summary loses fine-grained detail from older turns. An
alternative approach is full conversation summarization (compress everything
each turn), which saves more tokens but loses more detail. Our approach
is a practical middle ground.

---

### 6. Keyword-based sentiment over LLM-based sentiment
**Decision:** Simple keyword counting for sentiment scoring
**Reason:** Calling the LLM a second time purely for sentiment would double
the latency and cost per turn. Keyword matching is instant and sufficient
for coarse-grained quality tracking.
**Trade-off:** Less accurate than LLM-based or model-based sentiment
(e.g., a fine-tuned BERT classifier). For production, replacing this with
a lightweight sentiment model (VADER or distilbert-sentiment) would improve
accuracy with minimal latency impact.

---

### 7. Soft delete for conversations
**Decision:** `is_active=False` flag instead of actual deletion
**Reason:** Preserves data for analytics. A conversation that looks
"deleted" to the user still contributes to repair rate, sentiment trends,
and session length metrics.
**Trade-off:** Database grows indefinitely. A scheduled cleanup job
(hard delete conversations inactive for >90 days) would be the production
solution.

---

### 8. Seeded knowledge base over empty KB
**Decision:** Generate a representative Tech Support KB at startup
**Reason:** No domain data was provided with the assessment. An empty KB
would make RAG non-demonstrable. By seeding 17 documents across 3
meaningful categories, we can prove the full pipeline works end to end.
**Trade-off:** Synthetic data doesn't reflect real-world document
distribution. In production, the seed script would be replaced by an
ingestion pipeline that reads from real sources (Confluence, Zendesk,
PDFs, etc.).

---

## Performance Analysis

### Observed latencies (from testing)
| Turn | Latency |
|---|---|
| Turn 1 (password reset) | 15.78s |
| Turn 2 (no email received) | 24.59s |
| Turn 3 (repair turn) | 17.19s |
| Turn 4 (billing refund) | 19.86s |
| Turn 5 (API rate limits) | 16.16s |
| **Average** | **18.72s** |

### Latency breakdown (estimated)
| Stage | Time |
|---|---|
| usf-embed (query) | ~1-2s |
| ChromaDB retrieval | ~0.1s |
| usf-rerank | ~2-3s |
| usf1-mini generation | ~12-15s |
| DB read/write | ~0.1s |
| **Total** | **~15-20s** |

The dominant cost is the LLM generation step (~80% of total latency).

### Production optimizations
1. **Streaming responses** — stream LLM tokens to the client so the user
   sees output immediately instead of waiting 15s for the full response
2. **Embedding cache** — cache embeddings for repeated queries (Redis TTL)
3. **Async RAG** — run embedding + retrieval concurrently with history
   loading using `asyncio.gather`
4. **Connection pooling** — replace SQLite with PostgreSQL + pgbouncer

---

## Future Improvements

Given more time, the following would be high-priority additions:

### Short term
- **Streaming endpoint** (`POST /chat/stream`) using Server-Sent Events
- **Conversation search** — full-text search across message history
- **KB ingestion API** — `POST /knowledge-base/ingest` to add documents
  at runtime without reseeding
- **Rate limiting** — per-user request throttling with slowapi

### Medium term
- **Authentication** — JWT-based auth with user sessions
- **Async LLM calls** — convert all httpx calls to async for better
  concurrency under load
- **Better sentiment** — replace keyword scoring with a lightweight
  VADER or distilbert model
- **Conversation export** — `GET /conversations/{id}/export` as PDF or JSON

### Long term
- **Multi-tenant architecture** — organization-level isolation
- **A/B testing framework** — test different RAG strategies or prompts
  against each other using analytics metrics as the evaluation signal
- **Automated KB refresh** — scheduled job to re-embed and update
  documents when source content changes
- **Fine-tuned reranker** — train usf-rerank on domain-specific
  query-document pairs for better precision