import json
import math

DEFAULT_INDEX_PATH = "rules_index.json"
SIMILARITY_THRESHOLD = 0.3

_index_cache = None

def load_index(index_path: str = DEFAULT_INDEX_PATH) -> list:
    global _index_cache
    if _index_cache is None:
        with open(index_path, encoding="utf-8") as f:
            _index_cache = json.load(f)
    return _index_cache

def _cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def retrieve_context(query_embedding: list, top_k: int = 3, index: list = None) -> dict:
    if index is None:
        index = load_index()

    scored = [
        (entry, _cosine_similarity(query_embedding, entry["embedding"]))
        for entry in index
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    top_matches = [pair for pair in scored[:top_k] if pair[1] >= SIMILARITY_THRESHOLD]

    if not top_matches:
        return {"status": "no_match", "message": "no documents above similarity threshold"}

    return {
        "status": "success",
        "data": {
            "chunks": [entry["text"] for entry, _ in top_matches],
            "sources": [entry["source"] for entry, _ in top_matches],
        },
    }