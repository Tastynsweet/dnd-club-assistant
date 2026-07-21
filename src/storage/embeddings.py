_model = None

def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_text(text: str) -> list:
    model = get_model()
    return model.encode(text, convert_to_numpy=True).tolist()

def embed_batch(texts: list) -> list:
    model = get_model()
    return model.encode(texts, convert_to_numpy=True, show_progress_bar=True).tolist()