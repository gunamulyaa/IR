import streamlit as st
import json
import urllib.parse
import requests
import os

# === Konfigurasi Awal ===
DATA_PATH = os.path.join("Data", "combined_articles.json")
DEFAULT_IMAGE = "https://via.placeholder.com/800x400?text=Berita"

# === Fungsi generate URL gambar dari Unsplash ===
def generate_unsplash_url(title):
    keyword = urllib.parse.quote(" ".join(title.lower().split()[:2]))
    return f"https://source.unsplash.com/800x400/?{keyword},news"

# === Fungsi validasi gambar ===
def is_image_valid(url):
    try:
        response = requests.get(url, timeout=3)
        return response.status_code == 200 and "image" in response.headers.get("Content-Type", "")
    except:
        return False

# === Fungsi potong isi berita ===
def potong_isi(teks, max_kata=40):
    kata = teks.split()
    return " ".join(kata[:max_kata]) + "..." if len(kata) > max_kata else teks

# === Load data berita ===
try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        berita = json.load(f)
except FileNotFoundError:
    st.error(f"❌ File tidak ditemukan: {DATA_PATH}")
    st.stop()

# === UI Streamlit ===
st.title("📰 Pencarian Berita Online")
keyword = st.text_input("🔍 Masukkan kata kunci berita").strip().lower()

if keyword:
    hasil = [b for b in berita if keyword in b["title"].lower() or keyword in b["content"].lower()]
    st.markdown(f"### Ditemukan {len(hasil)} berita untuk: `{keyword}`")

    for b in hasil:
        st.subheader(b["title"])

        # Ambil gambar dari Unsplash (berdasarkan judul)
        img_url = generate_unsplash_url(b["title"])
        if is_image_valid(img_url):
            st.image(img_url, use_container_width=True)
        else:
            st.image(DEFAULT_IMAGE, use_container_width=True)

        st.write(potong_isi(b["content"]))
        st.markdown("---")
else:
    st.info("Masukkan kata kunci untuk mulai mencari berita.")
