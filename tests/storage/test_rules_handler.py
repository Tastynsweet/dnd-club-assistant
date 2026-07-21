from src.storage.rules_handler import retrieve_context

FAKE_INDEX = [
    {"id": 0, "text": "Grappling rules text.", "source": "SRD (section 0)", "embedding": [1.0, 0.0, 0.0]},
    {"id": 1, "text": "Advantage and disadvantage rules.", "source": "SRD (section 1)", "embedding": [0.0, 1.0, 0.0]},
    {"id": 2, "text": "Unrelated equipment text.", "source": "SRD (section 2)", "embedding": [0.0, 0.0, 1.0]},
]

def test_retrieve_context_returns_closest_match_first():
    query_embedding = [1.0, 0.0, 0.0]
    result = retrieve_context(query_embedding, top_k=2, index=FAKE_INDEX)

    assert result["status"] == "success"
    assert result["data"]["chunks"][0] == "Grappling rules text."
    assert result["data"]["sources"][0] == "SRD (section 0)"

def test_retrieve_context_respects_top_k():
    query_embedding = [1.0, 0.0, 0.0]
    result = retrieve_context(query_embedding, top_k=1, index=FAKE_INDEX)

    assert len(result["data"]["chunks"]) == 1

def test_retrieve_context_no_match_below_threshold():
    query_embedding = [0.1, 0.1, 0.1]
    result = retrieve_context(query_embedding, top_k=3, index=[
        {"id": 0, "text": "x", "source": "s", "embedding": [-1.0, -1.0, -1.0]},
    ])

    assert result["status"] == "no_match"
    assert "message" in result