import json
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

INDEX_PATH = Path(__file__).parent / "faiss.index"
META_PATH = Path(__file__).parent / "faiss_meta.json"
MODEL_NAME = "all-MiniLM-L6-v2"

def main():
    index = faiss.read_index(str(INDEX_PATH))
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))

    model = SentenceTransformer(MODEL_NAME)

    while True:
        q = input("\nquery> ").strip()
        if not q:
            break

        v = model.encode([q], normalize_embeddings=True)
        D, I = index.search(v.astype("float32"), 10)

        for rank, (score, idx) in enumerate(zip(D[0], I[0]), start=1):
            m = meta[idx]
            md = m.get("metadata", {})
            print(f"\n#{rank} score={score:.3f}")
            print("name:", md.get("name"))
            print("restaurant:", md.get("restaurant"))
            print("calories:", md.get("calories"))

if __name__ == "__main__":
    main()
