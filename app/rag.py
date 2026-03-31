import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.llm import get_embedding, rerank_texts

chroma_client = chromadb.PersistentClient(
    path=settings.CHROMA_DB_PATH,
    settings=ChromaSettings(anonymized_telemetry=False)
)

COLLECTION_NAME = "knowledge_base"


def get_collection():
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )


def add_documents(documents: list[dict]):
    """Add documents with real embeddings to ChromaDB."""
    collection = get_collection()
    collection.add(
        ids=[d["id"] for d in documents],
        documents=[d["text"] for d in documents],
        embeddings=[get_embedding(d["text"]) for d in documents],
        metadatas=[d.get("metadata", {}) for d in documents]
    )


def retrieve(query: str, n_results: int = 5) -> list[dict]:
    """Vector similarity search in ChromaDB."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    output = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        output.append({"text": doc, "metadata": meta, "distance": dist})

    return output


def rerank(query: str, chunks: list[dict]) -> list[dict]:
    """
    Use the usf-rerank model to rerank retrieved chunks.
    Falls back to distance-based ordering if reranker fails.
    """
    if not chunks:
        return []

    texts = [c["text"] for c in chunks]

    try:
        reranked = rerank_texts(query, texts)
        
        result = []
        for r in reranked:
            chunk = chunks[r["index"]].copy()
            chunk["rerank_score"] = r["score"]
            result.append(chunk)
        return result
    except Exception as e:
        print(f"[RAG] Reranker failed, falling back to distance order: {e}")
        return sorted(chunks, key=lambda x: x["distance"])


def retrieve_and_rerank(query: str, n_results: int = 5, top_k: int = 3) -> list[dict]:
    """Full pipeline: embed query -> retrieve -> rerank -> return top_k."""
    chunks = retrieve(query, n_results=n_results)
    reranked = rerank(query, chunks)
    return reranked[:top_k]