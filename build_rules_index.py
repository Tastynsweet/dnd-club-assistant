import json
import re
import sys

from pypdf import PdfReader

from src.storage.embeddings import embed_batch

TARGET_CHUNK_SIZE = 800
OVERLAP = 150

def extract_and_clean(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n\n"

    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def chunk_text(text: str, target_size: int = TARGET_CHUNK_SIZE, overlap: int = OVERLAP) -> list:
    words = text.split()
    chunks = []
    current_words = []
    current_len = 0

    for word in words:
        current_words.append(word)
        current_len += len(word) + 1
        if current_len >= target_size:
            chunks.append(" ".join(current_words))
            overlap_words = []
            overlap_len = 0
            for w in reversed(current_words):
                overlap_len += len(w) + 1
                overlap_words.insert(0, w)
                if overlap_len >= overlap:
                    break
            current_words = overlap_words
            current_len = overlap_len

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks

def build_index(pdf_path: str, output_path: str = "rules_index.json"):
    print(f"Extracting text from {pdf_path}...")
    text = extract_and_clean(pdf_path)
    print(f"Extracted {len(text)} characters.")

    chunks = chunk_text(text)
    print(f"Split into {len(chunks)} chunks. Generating embeddings (this may take a minute)...")

    embeddings = embed_batch(chunks)

    index = [
        {"id": i, "text": chunk, "source": f"SRD 5.1 (section {i})", "embedding": emb}
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(index, f)

    print(f"Saved {len(index)} chunks with embeddings to {output_path}.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python build_rules_index.py path/to/SRD.pdf")
        sys.exit(1)
    build_index(sys.argv[1])