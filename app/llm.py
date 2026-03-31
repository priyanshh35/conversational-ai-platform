import time
import httpx
from openai import OpenAI
from app.config import settings

HEADERS = {
    "x-api-key": settings.API_KEY,
    "Content-Type": "application/json"
}

_http_client = httpx.Client(
    headers={"x-api-key": settings.API_KEY},
    timeout=60.0
)

chat_client = OpenAI(
    api_key="placeholder",           # overridden by custom http client
    base_url=settings.CHAT_BASE_URL,
    http_client=_http_client
)

def get_embedding(text: str) -> list[float]:
    """Call the usf-embed endpoint to get a vector for a text string."""
    response = httpx.post(
        f"{settings.EMBED_BASE_URL}/embeddings",
        headers=HEADERS,
        json={
            "model": settings.EMBEDDING_MODEL,
            "input": text
        },
        timeout=30.0
    )
    response.raise_for_status()
    data = response.json()

    if "data" in data:
        return data["data"][0]["embedding"]
    elif "embeddings" in data:
        return data["embeddings"][0]
    else:
        raise ValueError(f"Unexpected embedding response: {list(data.keys())}")

def rerank_texts(query: str, texts: list[str]) -> list[dict]:
    """
    Call the usf-rerank endpoint.
    """
    if not texts:
        return []

    response = httpx.post(
        f"{settings.RERANK_BASE_URL}/reranker",
        headers=HEADERS,
        json={
            "model": settings.RERANK_MODEL,
            "query": query,
            "texts": texts
        },
        timeout=30.0
    )
    response.raise_for_status()
    data = response.json()

    if "results" in data:
        results = data["results"]
    elif "scores" in data:
        results = [{"index": i, "score": s} for i, s in enumerate(data["scores"])]
    else:
        results = [{"index": i, "score": 1.0} for i in range(len(texts))]

    return sorted(results, key=lambda x: x["score"], reverse=True)

def chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> tuple[str, float]:
    """Call the LLM. Returns (response_text, latency_seconds)."""
    start = time.time()
    response = chat_client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    latency = time.time() - start
    return response.choices[0].message.content, latency

def summarize_conversation(turns: list[dict]) -> str:
    """Summarize old conversation turns to compress history."""
    formatted = "\n".join(
        f"{t['role'].upper()}: {t['content']}" for t in turns
    )
    prompt = [
        {
            "role": "system",
            "content": "Summarize the following conversation in 3-5 sentences. Capture key facts, user intent, and any decisions made."
        },
        {"role": "user", "content": formatted}
    ]
    summary, _ = chat_completion(prompt, temperature=0.3, max_tokens=300)
    return summary