import requests, numpy as np, streamlit as st, math
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from settings import ES_HOST, ES_INDEX, MODEL_NAME, VECTOR_DIMS
import pandas as pd  # tambahkan ini

st.set_page_config(page_title="Elasticsearch + Streamlit (Hybrid Search)", layout="wide")
st.title("🔎 Elastic Search Artikel")

@st.cache_resource(show_spinner=False)
def load_model():
    return SentenceTransformer(MODEL_NAME)

model = load_model()

def es_search_lexical(q: str, size=20, from_=0):
    body = {
        "from": from_,
        "size": size,
        "query": {
            "multi_match": {
                "query": q,
                "fields": ["title^3", "content", "text"]
            }
        },
        "highlight": {
            "fields": {
                "title": {"number_of_fragments": 0},
                "content": {"fragment_size": 120, "no_match_size": 120},
                "text": {"fragment_size": 120, "no_match_size": 120}
            },
            "pre_tags": ["<mark>"], "post_tags": ["</mark>"]
        }
    }
    r = requests.post(f"{ES_HOST}/{ES_INDEX}/_search", json=body, timeout=30)
    r.raise_for_status()
    return r.json()["hits"]["hits"]

def es_search_semantic(query_vec: List[float], k=20, num_candidates=100):
    # Top-level knn (ES 8.12+)
    body = {
        "knn": {
            "field": "vector",
            "query_vector": query_vec,
            "k": k,
            "num_candidates": num_candidates
        },
        # optional: tambahkan filter bool di sini kalau perlu
        "_source": True
    }
    r = requests.post(f"{ES_HOST}/{ES_INDEX}/_search", json=body, timeout=30)
    r.raise_for_status()
    return r.json()["hits"]["hits"]

def rrf_merge(listA, listB, k=60):
    # Reciprocal Rank Fusion: score = Σ 1/(k + rank)
    def to_map(lst):
        return {h["_id"]: (i+1, h) for i, h in enumerate(lst)}
    A = to_map(listA); B = to_map(listB)
    ids = set(A.keys()) | set(B.keys())
    fused = []
    for _id in ids:
        rA = A[_id][0] if _id in A else 10**9
        rB = B[_id][0] if _id in B else 10**9
        score = 1.0/(k + rA) + 1.0/(k + rB)
        hit = A[_id][1] if _id in A else B[_id][1]
        fused.append((_id, score, hit))
    fused.sort(key=lambda x: x[1], reverse=True)
    return [h for _,_,h in fused]


def _rank_map(hits):
    return {h["_id"]: i+1 for i, h in enumerate(hits)}

def _to_rank_table(results, mode, lex_hits=None, sem_hits=None):
    lex_map = _rank_map(lex_hits) if lex_hits else {}
    sem_map = _rank_map(sem_hits) if sem_hits else {}

    rows = []
    for i, h in enumerate(results, start=1):
        src = h.get("_source", {})
        rid = src.get("id") or h.get("_id")
        title = src.get("title") or src.get("text") or "(tanpa judul)"
        snippet_src = (src.get("content") or src.get("text") or "")
        snippet = (snippet_src[:160] + "…") if len(snippet_src) > 160 else snippet_src

        row = {
            "Rank": i,
            "ID": rid,
            "Title": title,
            "Score": round(float(h.get("_score", 0.0)), 4),
            "Snippet": snippet
        }
        if mode == "Hybrid (RRF)":
            r_lex = lex_map.get(h["_id"])
            r_sem = sem_map.get(h["_id"])
            row["Rank (BM25)"] = r_lex
            row["Rank Semantic"]  = r_sem
            # skor RRF untuk transparansi (k=60 default)
            K = 60
            rrf = (1.0 / (K + (r_lex if r_lex else 10**9))) + (1.0 / (K + (r_sem if r_sem else 10**9)))
            row["RRF~Score"] = round(rrf, 6)

        rows.append(row)

    cols = ["Rank","ID","Title","Score"]
    if mode == "Hybrid (RRF)":
        cols += ["Rank (BM25)","Rank Semantic","RRF~Score"]
    cols += ["Snippet"]
    return pd.DataFrame(rows)[cols]


mode = st.radio("Mode", ["ElasticSearch (BM25)", "Semantic", "Hybrid (RRF)"], horizontal=True)
q = st.text_input("Ketik kueri …", "")
topk = st.slider("Top-K", 5, 50, 20)
if st.button("Cari") and q.strip():
    with st.spinner("Mencari…"):
        results = []
        if mode == "ElasticSearch (BM25)":
            results = es_search_lexical(q, size=topk)
        elif mode == "Semantic":
            qvec = model.encode(q, normalize_embeddings=True).astype(float).tolist()
            if len(qvec) != VECTOR_DIMS:
                st.error(f"Dimensi query ({len(qvec)}) ≠ VECTOR_DIMS ({VECTOR_DIMS}). Sesuaikan MODEL_NAME/VECTOR_DIMS.")
            results = es_search_semantic(qvec, k=topk)
        else:  # Hybrid
            lex = es_search_lexical(q, size=topk)
            qvec = model.encode(q, normalize_embeddings=True).astype(float).tolist()
            sem = es_search_semantic(qvec, k=topk)
            results = rrf_merge(lex, sem)[:topk]

    st.caption(f"Hasil: {len(results)} dokumen")
    for hit in results:
        src = hit.get("_source", {})
        title = src.get("title") or src.get("text") or "(tanpa judul)"
        st.markdown(f"### {title}")
        snippet = (src.get("content") or src.get("text") or "")[:400]
        st.write(snippet + ("…" if len(snippet)==400 else ""))
        st.write(f"ID: `{src.get('id','')}` | Skor: {hit.get('_score',0):.2f}")
        st.divider()
    
    st.caption(f"Hasil: {len(results)} dokumen")

    # siapkan df sesuai mode
    if mode == "Hybrid (RRF)":
        df = _to_rank_table(results, mode, lex_hits=lex, sem_hits=sem)  # gunakan list lex & sem yang sudah dihitung
    else:
        df = _to_rank_table(results, mode)

    st.dataframe(df, use_container_width=True, hide_index=True)

    # tombol unduh CSV
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download hasil (CSV)",
        data=csv_bytes,
        file_name="search_results.csv",
        mime="text/csv"
    )

else:
    st.info("Masukkan kueri, pilih mode, lalu klik **Cari**.")
