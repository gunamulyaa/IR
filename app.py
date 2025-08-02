import streamlit as st
import json
from collections import Counter

with open("berita.json", "r", encoding="utf-8") as f:
    berita = json.load(f)

st.title("📰 Pencarian Berita")

semua_kata = []
for b in berita:
    semua_kata += b["judul"].lower().split()

top_kata = [k for k, _ in Counter(semua_kata).most_common(10) if len(k) > 3]

pilihan = st.selectbox("💡 Pilih topik populer", options=[""] + top_kata)
keyword_input = st.text_input("🔍 Atau ketik kata kunci sendiri").strip().lower()
keyword = keyword_input if keyword_input else pilihan

if keyword:
    hasil = [b for b in berita if keyword in b["judul"].lower() or keyword in b["isi"].lower()]
    st.markdown(f"### 🔎 {len(hasil)} hasil ditemukan untuk: `{keyword}`")
    for b in hasil:
        st.subheader(b["judul"])
        st.write(b["isi"])
        st.markdown(f"[Baca Selengkapnya]({b['link']})")
        st.markdown("---")
else:
    st.info("Silakan pilih atau ketik kata kunci untuk mulai mencari berita.")
