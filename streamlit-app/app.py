import requests, numpy as np, streamlit as st, math
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from settings import ES_HOST, ES_INDEX, MODEL_NAME, VECTOR_DIMS
import pandas as pd
from eval_metrics import (
    precision_at_k, recall_at_k, mean_reciprocal_rank,
    ndcg_at_k, mean_ndcg_at_k, average_precision, mean_average_precision,
    f1_at_k, r_precision, hit_rate_at_k
)

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

# --- sebelum UI utama ---
if "results" not in st.session_state:
    st.session_state.results = []
if "topk" not in st.session_state:
    st.session_state.topk = 20
if "mode" not in st.session_state:
    st.session_state.mode = None

with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.setdefault("RRF_K", 60)
    st.session_state.RRF_K = st.slider("RRF k", 10, 200, st.session_state.RRF_K, help="Semakin besar, kontribusi rank lebih datar.")
    st.session_state.setdefault("NUM_CANDIDATES", 100)
    st.session_state.NUM_CANDIDATES = st.slider("Semantic num_candidates", 20, 1000, st.session_state.NUM_CANDIDATES, step=20)


mode = st.radio("Mode", ["ElasticSearch (BM25)", "Semantic", "Hybrid (RRF)"], horizontal=True)
q = st.text_input("Ketik kueri …", "")
topk = st.slider("Top-K", 5, 50, 20)

# --- tombol cari ---
if st.button("Cari") and q.strip():
    with st.spinner("Mencari…"):
        if mode == "ElasticSearch (BM25)":
            results = es_search_lexical(q, size=topk)
            lex = sem = None
        elif mode == "Semantic":
            qvec = model.encode(q, normalize_embeddings=True).astype(float).tolist()
            if len(qvec) != VECTOR_DIMS:
                st.error(f"Dimensi query ({len(qvec)}) ≠ VECTOR_DIMS ({VECTOR_DIMS}). Sesuaikan MODEL_NAME/VECTOR_DIMS.")
            results = es_search_semantic(qvec, k=topk)
            lex = sem = None
        else:  # Hybrid
            lex = es_search_lexical(q, size=topk)
            qvec = model.encode(q, normalize_embeddings=True).astype(float).tolist()
            sem = es_search_semantic(qvec, k=topk)
            results = rrf_merge(lex, sem)[:topk]

    # simpan ke session_state agar tetap ada setelah rerun
    st.session_state.results = results
    st.session_state.topk = topk
    st.session_state.mode = mode
    # opsional: simpan juga lex & sem jika ingin menampilkan kolom pembanding
    st.session_state.lex_hits = lex if mode == "Hybrid (RRF)" else None
    st.session_state.sem_hits = sem if mode == "Hybrid (RRF)" else None





# ====== AUTO BENCHMARK (batch evaluate Semua Kueri) ======
with st.expander("🧪 Auto Benchmark (Offline Evaluation)", expanded=False):
    st.markdown("""
    Unggah **queries.csv** dan **qrels.csv** untuk evaluasi batch.
    - **queries.csv**: `query_id,query_text`
    - **qrels.csv**: `query_id,doc_id,grade` (0–3; 0=tidak relevan)
    """)

    colA, colB, colC = st.columns([1,1,1])
    with colA:
        queries_file = st.file_uploader("Upload queries.csv", type=["csv"], key="queries_csv")
    with colB:
        qrels_file = st.file_uploader("Upload qrels.csv", type=["csv"], key="qrels_csv")
    with colC:
        k_eval = st.number_input("k untuk metrik @k", min_value=1, max_value=100, value=10, step=1)

    run_bm25 = st.checkbox("Evaluasi BM25", value=True)
    run_sem  = st.checkbox("Evaluasi Semantic", value=True)
    run_hyb  = st.checkbox("Evaluasi Hybrid (RRF)", value=True)

    if st.button("▶️ Jalankan Benchmark"):
        if not queries_file or not qrels_file:
            st.error("Harap unggah **queries.csv** dan **qrels.csv** terlebih dahulu.")
        else:
            try:
                qdf = pd.read_csv(queries_file)
                rdf = pd.read_csv(qrels_file)

                # Validasi kolom
                required_q = {"query_id", "query_text"}
                required_r = {"query_id", "doc_id", "grade"}
                if not required_q.issubset(qdf.columns):
                    st.error(f"queries.csv harus punya kolom {required_q}")
                    st.stop()
                if not required_r.issubset(rdf.columns):
                    st.error(f"qrels.csv harus punya kolom {required_r}")
                    st.stop()

                # Susun qrels graded & biner
                qrels_graded: Dict[str, Dict[str, int]] = {}
                qrels_bin: Dict[str, set] = {}
                for _, row in rdf.iterrows():
                    qid = str(row["query_id"])
                    did = str(row["doc_id"])
                    grade = int(row["grade"])
                    qrels_graded.setdefault(qid, {})[did] = grade
                    if grade > 0:
                        qrels_bin.setdefault(qid, set()).add(did)
                    else:
                        qrels_bin.setdefault(qid, set())

                queries = [(str(r["query_id"]), str(r["query_text"])) for _, r in qdf.iterrows()]
                systems = []
                if run_bm25: systems.append("ElasticSearch (BM25)")
                if run_sem:  systems.append("Semantic")
                if run_hyb:  systems.append("Hybrid (RRF)")
                if not systems:
                    st.warning("Pilih minimal satu sistem untuk dievaluasi.")
                    st.stop()

                # Helper lokal: jalankan satu kueri di mode tertentu
                def _run_one_query(qtext: str, topk: int, mode: str):
                    if mode == "ElasticSearch (BM25)":
                        hits = es_search_lexical(qtext, size=topk)
                    elif mode == "Semantic":
                        qvec = model.encode(qtext, normalize_embeddings=True).astype(float).tolist()
                        if len(qvec) != VECTOR_DIMS:
                            raise ValueError(f"Dimensi query ({len(qvec)}) ≠ VECTOR_DIMS ({VECTOR_DIMS}).")
                        hits = es_search_semantic(qvec, k=topk)
                    else:
                        lex = es_search_lexical(qtext, size=topk)
                        qvec = model.encode(qtext, normalize_embeddings=True).astype(float).tolist()
                        sem = es_search_semantic(qvec, k=topk)
                        hits = rrf_merge(lex, sem)[:topk]
                    doc_ids = [str(h.get("_source", {}).get("id") or h.get("_id")) for h in hits]
                    return hits, doc_ids

                summary_rows = []
                perquery_rows = []

                for sys_name in systems:
                    runs: Dict[str, List[str]] = {}
                    st.write(f"Menjalankan: **{sys_name}** …")
                    prog = st.progress(0)
                    for i, (qid, qtext) in enumerate(queries, start=1):
                        _, doc_ids = _run_one_query(qtext, topk=k_eval, mode=sys_name)
                        runs[qid] = doc_ids

                        # per-kueri
                        relmap = qrels_graded.get(qid, {})
                        rel_list_ranked = [relmap.get(d, 0) for d in doc_ids]
                        ndcg = ndcg_at_k(rel_list_ranked, k_eval, use_exp_gain=True)

                        relset = qrels_bin.get(qid, set())
                        prec = precision_at_k(relset, doc_ids, k_eval)
                        rec  = recall_at_k(relset, doc_ids, k_eval)
                        # MRR per kueri
                        rr = 0.0
                        for rank, d in enumerate(doc_ids, start=1):
                            if d in relset:
                                rr = 1.0 / rank
                                break

                        perquery_rows.append({
                            "system": sys_name,
                            "query_id": qid,
                            "query_text": qtext,
                            f"P@{k_eval}": round(prec, 4),
                            f"R@{k_eval}": round(rec, 4),
                            "MRR": round(rr, 4),
                            f"nDCG@{k_eval}": round(ndcg, 4),
                        })
                        prog.progress(i / len(queries))

                    # agregasi sistem
                    mapv = mean_average_precision({q: list(s) for q, s in qrels_bin.items()}, runs)

                    mrrv_all, cnt = 0.0, 0
                    for qid, relset in qrels_bin.items():
                        if not relset: 
                            continue
                        ranked = runs.get(qid, [])
                        rr = 0.0
                        for rank, d in enumerate(ranked, start=1):
                            if d in relset:
                                rr = 1.0 / rank
                                break
                        mrrv_all += rr; cnt += 1
                    mrrv_all = (mrrv_all / cnt) if cnt else 0.0

                    ndcgs = []
                    for qid, _ in queries:
                        relmap = qrels_graded.get(qid, {})
                        ranked = runs.get(qid, [])
                        rel_list_ranked = [relmap.get(d, 0) for d in ranked]
                        ndcgs.append(ndcg_at_k(rel_list_ranked, k_eval, use_exp_gain=True))
                    ndcg_mean = sum(ndcgs) / len(ndcgs) if ndcgs else 0.0

                    p_mean, r_mean = [], []
                    for qid, _ in queries:
                        relset = qrels_bin.get(qid, set())
                        ranked = runs.get(qid, [])
                        p_mean.append(precision_at_k(relset, ranked, k_eval))
                        r_mean.append(recall_at_k(relset, ranked, k_eval))
                    p_mean = sum(p_mean)/len(p_mean) if p_mean else 0.0
                    r_mean = sum(r_mean)/len(r_mean) if r_mean else 0.0

                    summary_rows.append({
                        "system": sys_name,
                        f"P@{k_eval}": round(p_mean, 4),
                        f"R@{k_eval}": round(r_mean, 4),
                        "MRR": round(mrrv_all, 4),
                        "MAP": round(mapv, 4),
                        f"nDCG@{k_eval}": round(ndcg_mean, 4),
                    })

                st.subheader("Ringkasan per Sistem")
                df_sum = pd.DataFrame(summary_rows).sort_values(by=f"nDCG@{k_eval}", ascending=False)
                st.dataframe(df_sum, use_container_width=True, hide_index=True)
                st.download_button(
                    "⬇️ Unduh Ringkasan (CSV)",
                    data=df_sum.to_csv(index=False).encode("utf-8"),
                    file_name="benchmark_summary.csv",
                    mime="text/csv"
                )

                st.subheader("Hasil per Kueri")
                df_detail = pd.DataFrame(perquery_rows)
                st.dataframe(df_detail, use_container_width=True, hide_index=True)
                st.download_button(
                    "⬇️ Unduh Detail (CSV)",
                    data=df_detail.to_csv(index=False).encode("utf-8"),
                    file_name="benchmark_detail.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"Gagal menjalankan benchmark: {e}")


# ====== POOLING UNTUK ANOTASI ======
with st.expander("🧰 Buat Pool untuk Anotasi (qrels draft)", expanded=False):
    st.markdown("Masukkan beberapa kueri (satu per baris) untuk membuat pool top-K dari BM25, Semantic, dan Hybrid.")
    q_multi = st.text_area("Daftar kueri", height=120, placeholder="contoh:\nobat demam anak\nteknik audit keamanan jaringan")
    k_pool = st.slider("Top-K per sistem", 5, 100, 20)
    if st.button("📦 Bangun Pool"):
        try:
            rows = []
            for qline in [x.strip() for x in q_multi.splitlines() if x.strip()]:
                # jalankan 3 sistem
                lex = es_search_lexical(qline, size=k_pool)
                qvec = model.encode(qline, normalize_embeddings=True).astype(float).tolist()
                sem = es_search_semantic(qvec, k=k_pool)
                hyb = rrf_merge(lex, sem)[:k_pool]

                def _collect(hits, system):
                    for rank, h in enumerate(hits, start=1):
                        did = str(h.get("_source", {}).get("id") or h.get("_id"))
                        title = h.get("_source", {}).get("title") or h.get("_source", {}).get("text") or ""
                        rows.append({
                            "query_text": qline,
                            "system": system,
                            "rank": rank,
                            "doc_id": did,
                            "title": title,
                            "grade": ""  # diisi anotator: 0,1,2,3
                        })

                _collect(lex, "BM25")
                _collect(sem, "Semantic")
                _collect(hyb, "Hybrid")

            pool_df = pd.DataFrame(rows).drop_duplicates(subset=["query_text","doc_id"], keep="first")
            st.dataframe(pool_df, use_container_width=True, hide_index=True)
            st.download_button(
                "⬇️ Unduh Template qrels (CSV)",
                data=pool_df.to_csv(index=False).encode("utf-8"),
                file_name="qrels_template_to_label.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Gagal membuat pool: {e}")


# ====== DIAGNOSTIK HYBRID (kueri aktif) ======
with st.expander("🔬 Diagnostik Hybrid untuk kueri ini", expanded=False):
    if st.session_state.mode == "Hybrid (RRF)" and st.session_state.lex_hits and st.session_state.sem_hits:
        # peta rank
        lex_map = {h["_id"]: i+1 for i, h in enumerate(st.session_state.lex_hits)}
        sem_map = {h["_id"]: i+1 for i, h in enumerate(st.session_state.sem_hits)}

        diag_rows = []
        for i, h in enumerate(st.session_state.results, start=1):
            _id = h["_id"]
            src = h.get("_source", {})
            title = src.get("title") or src.get("text") or "(tanpa judul)"
            r_lex = lex_map.get(_id)
            r_sem = sem_map.get(_id)
            K = 60
            rrf = (1/(K + (r_lex if r_lex else 10**9))) + (1/(K + (r_sem if r_sem else 10**9)))
            diag_rows.append({
                "HybridRank": i,
                "Title": title[:80],
                "Rank(BM25)": r_lex,
                "Rank(Semantic)": r_sem,
                "RRF~Score": round(rrf, 6)
            })
        st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Diagnostik tersedia jika mode **Hybrid (RRF)** dan kamu baru saja melakukan pencarian.")


# --- render hasil (selalu tampil jika sudah ada hasil di session_state) ---
if st.session_state.results:
    results = st.session_state.results
    mode = st.session_state.mode
    topk = st.session_state.topk
    lex = getattr(st.session_state, "lex_hits", None)
    sem = getattr(st.session_state, "sem_hits", None)

    st.caption(f"Hasil: {len(results)} dokumen")
    for hit in results:
        src = hit.get("_source", {})
        title = src.get("title") or src.get("text") or "(tanpa judul)"
        st.markdown(f"### {title}")
        snippet = (src.get("content") or src.get("text") or "")[:400]
        st.write(snippet + ("…" if len(snippet)==400 else ""))
        st.write(f"ID: `{src.get('id','')}` | Skor: {hit.get('_score',0):.2f}")
        st.divider()

    # siapkan df sesuai mode
    if mode == "Hybrid (RRF)":
        df = _to_rank_table(results, mode, lex_hits=lex, sem_hits=sem)
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

    # --- Evaluasi (SEKARANG di luar blok tombol 'Cari') ---
    st.subheader("Evaluasi Hasil Pencarian")
    st.markdown("Masukkan daftar ID relevan (ground truth) untuk kueri ini, pisahkan dengan koma:")
    qrels_input = st.text_input("ID relevan (misal: 868,866)", key="qrels_input")

    # gunakan form agar klik 'Evaluasi' tidak bentrok dengan tombol lain
    with st.form("eval_form"):
        submit_eval = st.form_submit_button("Evaluasi")
        if submit_eval:
            try:
                relevant_ids = [x.strip() for x in (st.session_state.get("qrels_input") or "").split(",") if x.strip()]
                retrieved_ids = []
                for hit in results:
                    src = hit.get("_source", {})
                    rid = str(src.get("id") or hit.get("_id"))
                    retrieved_ids.append(rid)
                k = topk
                prec = precision_at_k(relevant_ids, retrieved_ids, k)
                rec = recall_at_k(relevant_ids, retrieved_ids, k)
                mrr = mean_reciprocal_rank({"q": relevant_ids}, {"q": retrieved_ids})
                st.write(f"**Precision@{k}:** {prec:.3f}")
                st.write(f"**Recall@{k}:** {rec:.3f}")
                st.write(f"**MRR:** {mrr:.3f}")
            except Exception as e:
                st.error(f"Terjadi error saat evaluasi: {e}")
else:
    st.info("Masukkan kueri, pilih mode, lalu klik **Cari**.")
