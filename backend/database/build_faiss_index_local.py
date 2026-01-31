import json
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

JSONL_PATH = Path(__file__).parent / "rag_items.jsonl"
OUT_INDEX = Path(__file__).parent / "faiss.index"
OUT_META = Path(__file__).parent / "faiss_meta.json"

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH = 64

def load_items():
    items = []
    with JSONL_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
    return items

def main():
    items = load_items()
    texts = [it["embedding_text"] for it in items]

    model = SentenceTransformer(MODEL_NAME)

    vectors = []
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i+BATCH]
        embs = model.encode(
            chunk,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        vectors.extend(embs)
        print(f"embedded {min(i+BATCH, len(texts))}/{len(texts)}")

    X = np.array(vectors, dtype="float32")
    dim = X.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(X)
    faiss.write_index(index, str(OUT_INDEX))

    meta = []
    for it in items:
        meta.append({
            "id": it["id"],
            "spoonacular_id": it.get("spoonacular_id"),
            "metadata": it.get("metadata", {}),
        })

    OUT_META.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    print(f"\nFAISS index written:")
    print(f"- vectors: {index.ntotal}")
    print(f"- dim: {dim}")
    print(f"- index: {OUT_INDEX}")
    print(f"- meta: {OUT_META}")

if __name__ == "__main__":
    main()
