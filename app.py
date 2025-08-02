import streamlit as st
import json
import urllib.parse
import os

# === Path file JSON ===
DATA_PATH = os.path.join("Data", "combined_articles.json")

# === Fungsi buat gambar Unsplash ===
def generate_unsplash_url(title):
    keyword = urllib.parse.quote(" ".join(title.lower().split()[:2]))
    return f"https://source.unsplash.com/800x400/?{keyword}"

# === Fungsi potong isi ===
def potong_isi(teks, max_kata=40):
    kata = teks.split()
    return " ".join(kata[:max_kata]) + "..." if len(kata) > max_kata else teks

# === Load data JSON ===
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        berita = json.load(f)
except FileNotFoundError:
    st.error(f"❌ File tidak ditemukan: {DATA_PATH}")
    st.stop()

# === UI Streamlit ===
st.title("📰 Pencarian Berita")

keyword = st.text_input("🔍 Masukkan kata kunci").strip().lower()

if keyword:
    hasil = [b for b in berita if keyword in b["title"].lower() or keyword in b["content"].lower()]
    st.markdown(f"### Ditemukan {len(hasil)} berita untuk: `{keyword}`")

    for b in hasil:
        st.subheader(b["title"])

        # TANPA validasi: langsung tampilkan
        img_url = generate_unsplash_url(b["title"])
        st.image(img_url, use_container_width=True)

        st.write(potong_isi(b["content"]))
        st.markdown("---")
else:
    st.info("Masukkan kata kunci untuk mulai mencari berita.")
