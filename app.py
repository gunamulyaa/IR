import streamlit as st
import os
from elasticsearch import Elasticsearch
from steps.preprocessing import run_preprocessing
from steps.embedding import run_embedding
from steps.indexing import run_indexing
from steps.retrieval import run_retrieval

# File paths
DATA_RAW = "Data/combined_articles.json"
DATA_PREPROCESSED = "Data/preprocessed.json"
DATA_EMBEDDED = "Data/embedded.json"

# Elasticsearch config
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", None)
ES_PASS = os.getenv("ES_PASS", None)

# Connect to Elasticsearch
if ES_USER and ES_PASS:
    es = Elasticsearch(hosts=[ES_HOST], basic_auth=(ES_USER, ES_PASS))
else:
    es = Elasticsearch(hosts=[ES_HOST])

# Run pipeline automatically once
@st.cache_resource
def init_pipeline():
    if not os.path.exists(DATA_PREPROCESSED):
        st.info("🔄 Menjalankan preprocessing...")
        run_preprocessing(DATA_RAW, DATA_PREPROCESSED)

    if not os.path.exists(DATA_EMBEDDED):
        st.info("🔄 Membuat embedding...")
        run_embedding(DATA_PREPROCESSED, DATA_EMBEDDED)

    st.info("🔄 Indexing ke Elasticsearch...")
    run_indexing(es, DATA_EMBEDDED)
    st.success("✅ Pipeline selesai.")

init_pipeline()

# UI Search
st.title("🔍 Pencarian Berita (Fokus Content)")
query = st.text_input("Masukkan kata kunci / kalimat:")
top_k = st.slider("Jumlah hasil", 1, 20, 5)

if st.button("Cari") and query.strip():
    results = run_retrieval(es, query, k=top_k)
    if results:
        for r in results:
            st.markdown(f"### {r['title']}")
            st.write(r['content'])
            st.caption(f"Score: {r['score']:.4f}")
            st.markdown("---")
    else:
        st.warning("Tidak ada hasil ditemukan.")
