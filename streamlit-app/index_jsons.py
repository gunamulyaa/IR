import json, requests, sys, pathlib
from settings import ES_HOST, ES_INDEX, VECTOR_DIMS

def read_json_or_jsonl(path):
    p = pathlib.Path(path)
    if p.suffix.lower() == ".jsonl":
        rows = []
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    else:
        # .json array
        return json.loads(p.read_text(encoding="utf-8"))

def build_embed_map(emb_rows):
    m = {}
    for r in emb_rows:
        rid = str(r.get("id"))
        emb = r.get("embedding")
        if emb is None or len(emb) != VECTOR_DIMS:
            raise ValueError(f"Dimensi embedding untuk id={rid} tidak cocok dengan VECTOR_DIMS={VECTOR_DIMS}")
        m[rid] = {
            "text": r.get("text", ""),
            "embedding": emb
        }
    return m

def bulk_index(joined_rows):
    lines = []
    for rec in joined_rows:
        meta = {"index": {"_index": ES_INDEX, "_id": rec["id"]}}
        source = {
            "id": rec["id"],
            "title": rec.get("title",""),
            "content": rec.get("content",""),
            "text": rec.get("text",""),
            "vector": rec["embedding"]
        }
        lines.append(json.dumps(meta, ensure_ascii=False))
        lines.append(json.dumps(source, ensure_ascii=False))
    payload = "\n".join(lines) + "\n"
    r = requests.post(f"{ES_HOST}/_bulk", data=payload.encode("utf-8"),
                      headers={"Content-Type":"application/x-ndjson"})
    r.raise_for_status()
    res = r.json()
    if res.get("errors"):
        errors = [it for it in res["items"] if it.get("index", {}).get("error")]
        raise RuntimeError(f"Ada error bulk. Contoh: {errors[:3]}")
    print(f"Indeks OK: {len(joined_rows)} dokumen")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Pemakaian: python index_jsons.py /data/corpus.json /data/embeddings.jsonl")
        sys.exit(1)

    corpus = read_json_or_jsonl(sys.argv[1])
    embs   = read_json_or_jsonl(sys.argv[2])

    emb_map = build_embed_map(embs)

    joined = []
    missing = []
    for r in corpus:
        rid = str(r.get("id"))
        if rid in emb_map:
            joined.append({
                "id": rid,
                "title": r.get("title",""),
                "content": r.get("content",""),
                "text": emb_map[rid]["text"],
                "embedding": emb_map[rid]["embedding"]
            })
        else:
            missing.append(rid)

    if missing:
        print(f"Peringatan: {len(missing)} id di corpus tidak punya embedding, contoh: {missing[:5]}")

    bulk_index(joined)
