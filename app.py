import streamlit as st
import json
from collections import Counter
import os
import urllib.parse

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
    semua_kata += b["title"].lower().split()

top_kata = [k for k, _ in Counter(semua_kata).most_common(10) if len(k) > 3]

# ==== UI Search ====
saran = st.selectbox("💡 Pilih topik populer (opsional)", [""] + top_kata)
keyword_input = st.text_input("🔍 Atau ketik kata kunci sendiri").strip().lower()
keyword = keyword_input if keyword_input else saran

def potong_isi(teks, max_kata=40):
    kata = teks.split()
    if len(kata) > max_kata:
        return " ".join(kata[:max_kata]) + "..."
    return teks

def generate_unsplash_url(title):
    # Ambil 1–2 kata pertama dari judul untuk dijadikan keyword pencarian gambar
    keyword = " ".join(title.lower().split()[:2])
    keyword = urllib.parse.quote(keyword)  # encode URL
    return f"https://source.unsplash.com/800x400/?{keyword},news"

# ==== Filter berita berdasarkan keyword ====
for b in hasil:
    st.subheader(b["title"])

    # Gambar dari Unsplash berdasarkan isi judul
    img_url = generate_unsplash_url(b["title"])
    st.image(img_url, use_column_width=True)

    st.write(potong_isi(b["content"]))

    if "link" in b:
        st.markdown(f"[📖 Baca Selengkapnya]({b['link']})")

    st.markdown("---")
