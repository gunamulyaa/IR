import streamlit as st
import json
from collections import Counter
import os

# ==== Load data dari file JSON ====
DATA_PATH = os.path.join("Data", "combined_articles.json")

try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        berita = json.load(f)
except FileNotFoundError:
    st.error(f"Gagal memuat data dari {DATA_PATH}. Pastikan file ada.")
    st.stop()

# ==== Judul Aplikasi ====
st.title("📰 Pencarian Berita Online")

# ==== Ambil keyword populer dari judul ====
semua_kata = []
for b in berita:
    semua_kata += b["judul"].lower().split()

top_kata = [k for k, _ in Counter(semua_kata).most_common(10) if len(k) > 3]

# ==== UI Search ====
saran = st.selectbox("💡 Pilih topik populer (opsional)", [""] + top_kata)
keyword_input = st.text_input("🔍 Atau ketik kata kunci sendiri").strip().lower()
keyword = keyword_input if keyword_input else saran

# ==== Filter berita berdasarkan keyword ====
if keyword:
    hasil = [b for b in berita if keyword in b["judul"].lower() or keyword in b["isi"].lower()]
    st.markdown(f"### 🔎 {len(hasil)} hasil ditemukan untuk: `{keyword}`")

    for b in hasil:
        st.subheader(b["judul"])
        st.write(b["isi"])
        if "link" in b:
            st.markdown(f"[Baca Selengkapnya]({b['link']})")
        st.markdown("---")
else:
    st.info("Silakan pilih atau ketik kata kunci untuk mencari berita.")
