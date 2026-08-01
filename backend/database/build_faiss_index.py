import json
from pathlib import Path

import numpy as np
import faiss
from openai import OpenAI

JSONL_PATH = Path(__file__).parent / "rag_items.jsonl"
OUT_INDEX = Path(__file__).parent / "faiss.index"
OUT_META = Path(__file__).parent / "faiss_meta.json"

MODEL = "text-embedding-3-large"  # most capable embedding model :contentReference[oaicite:0]{index=0}
BATCH = 128

def load_items():
    items = []
    with JSONL_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
    return items

def embed_texts(client: OpenAI, texts):
    # OpenAI embeddings API supports batching with array inputs :contentReference[oaicite:1]{index=1}
    resp = client.embeddings.create(model=MODEL, input=texts)
    # keep order stable
    return [d.embedding for d in resp.data]

def main():
    client = OpenAI()
    items = load_items()
    texts = [it["embedding_text"] for it in items]

    vectors = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i+BATCH]
        embs = embed_texts(client, chunk)
        vectors.extend(embs)
        print(f"embedded {min(i+BATCH, len(texts))}/{len(texts)}")

    X = np.array(vectors, dtype="float32")
    dim = X.shape[1]

    # cosine similarity = inner product on normalized vectors
    faiss.normalize_L2(X)
    index = faiss.IndexFlatIP(dim)
    index.add(X)

    faiss.write_index(index, str(OUT_INDEX))

    # store metadata with same ordering as vectors
    meta = []
    for it in items:
        meta.append({
            "id": it["id"],
            "spoonacular_id": it.get("spoonacular_id"),
            "metadata": it.get("metadata", {}),
        })
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote FAISS index: {OUT_INDEX}")
    print(f"Wrote metadata:  {OUT_META}")
    print(f"Vectors: {index.ntotal}, dim={dim}")

if __name__ == "__main__":
    main()
