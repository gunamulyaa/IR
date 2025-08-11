import json
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

MODEL_NAME = "all-MiniLM-L6-v2"

def run_embedding(input_path, output_path):
    model = SentenceTransformer(MODEL_NAME)
    with open(input_path, "r", encoding="utf-8") as f:
        passages = json.load(f)

    for p in tqdm(passages, desc="Embedding"):
        p["content_vector"] = model.encode(p["content"], normalize_embeddings=True).tolist()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(passages, f, ensure_ascii=False)

    return len(passages)
