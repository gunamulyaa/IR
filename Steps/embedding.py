import json
import os
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

MODEL_NAME = "all-MiniLM-L6-v2"

def run_embedding(input_path, output_path):
    # Cek file input
    if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
        raise ValueError(f"[ERROR] File input kosong atau tidak ada: {input_path}")

    # Load data
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            passages = json.load(f)
        except json.JSONDecodeError:
            raise ValueError(f"[ERROR] Format JSON tidak valid di {input_path}")

    if not passages:
        raise ValueError("[ERROR] Tidak ada data yang ditemukan untuk di-embedding.")

    # Load model
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        raise RuntimeError(f"[ERROR] Gagal memuat model '{MODEL_NAME}': {str(e)}")

    # Proses embedding
    try:
        for p in tqdm(passages, desc="Embedding"):
            if not p.get("content"):
                raise ValueError(f"[ERROR] Data passage kosong: {p}")
            p["content_vector"] = model.encode(
                p["content"], normalize_embeddings=True
            ).tolist()
    except Exception as e:
        raise RuntimeError(f"[ERROR] Gagal membuat embedding: {str(e)}")

    # Simpan output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(passages, f, ensure_ascii=False)

    print(f"[INFO] Embedding selesai. Disimpan di: {output_path}")
    return len(passages)
