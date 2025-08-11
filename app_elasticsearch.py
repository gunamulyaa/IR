import streamlit as st
import json
import urllib.parse
import os
from datetime import datetime
import pandas as pd
from elasticsearch_manager import ElasticsearchManager, load_articles_from_json

# === Konfigurasi Page ===
st.set_page_config(
    page_title="📰 Sistem Pencarian Berita IR",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === Path file JSON ===
DATA_PATH = os.path.join("Data", "combined_articles.json")

# === Fungsi Utility ===
@st.cache_data
def load_articles():
    """Load artikel dengan caching untuk performa better"""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ File tidak ditemukan: {DATA_PATH}")
        return []

def potong_isi(teks, max_kata=40):
    """Potong isi artikel untuk preview"""
    if not teks:
        return ""
    kata = teks.split()
    return " ".join(kata[:max_kata]) + "..." if len(kata) > max_kata else teks

def format_date(date_str):
    """Format tanggal untuk tampilan yang lebih baik"""
    try:
        if isinstance(date_str, str):
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d %B %Y, %H:%M")
    except:
        pass
    return date_str

def highlight_text(text, query):
    """Highlight kata kunci dalam teks"""
    if not query or not text:
        return text
    
    # Simple highlighting untuk fallback
    words = query.lower().split()
    highlighted = text
    for word in words:
        if len(word) > 2:  # Hanya highlight kata yang cukup panjang
            highlighted = highlighted.replace(
                word, f"<mark style='background-color: yellow; padding: 2px;'>{word}</mark>"
            )
            # Case insensitive
            highlighted = highlighted.replace(
                word.capitalize(), f"<mark style='background-color: yellow; padding: 2px;'>{word.capitalize()}</mark>"
            )
    return highlighted

# === Initialize Elasticsearch ===
@st.cache_resource
def get_elasticsearch_manager():
    """Initialize Elasticsearch manager dengan caching"""
    return ElasticsearchManager()

# === Main App ===
def main():
    # Header
    st.title("📰 Sistem Pencarian Berita Indonesia")
    st.markdown("---")
    
    # Initialize Elasticsearch
    es_manager = get_elasticsearch_manager()
    
    # Sidebar untuk konfigurasi
    with st.sidebar:
        st.header("⚙️ Konfigurasi Pencarian")
        
        # Mode pencarian
        search_mode = st.selectbox(
            "Mode Pencarian:",
            ["🚀 Elasticsearch (Advanced)", "📝 Simple Search"]
        )
        
        # Elasticsearch status
        if search_mode.startswith("🚀"):
            es_connected = es_manager.is_connected()
            if es_connected:
                st.success("✅ Elasticsearch Connected")
                
                # Elasticsearch stats
                with st.expander("📊 Statistics"):
                    stats = es_manager.get_article_stats()
                    if stats:
                        st.metric("Total Articles", stats.get('total_articles', 0))
                        if 'date_stats' in stats:
                            date_stats = stats['date_stats']
                            if 'min_as_string' in date_stats:
                                st.write(f"📅 Oldest: {date_stats['min_as_string'][:10]}")
                            if 'max_as_string' in date_stats:
                                st.write(f"📅 Newest: {date_stats['max_as_string'][:10]}")
            else:
                st.error("❌ Elasticsearch Disconnected")
                st.warning("Menggunakan pencarian sederhana...")
                search_mode = "📝 Simple Search"
        
        # Pengaturan hasil
        st.subheader("🎛️ Pengaturan Hasil")
        results_per_page = st.slider("Hasil per halaman:", 5, 50, 10)
        show_content_preview = st.checkbox("Tampilkan preview konten", True)
        show_highlights = st.checkbox("Tampilkan highlight", True)
    
    # Load data
    berita = load_articles()
    if not berita:
        st.stop()
    
    # Search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        keyword = st.text_input(
            "🔍 Masukkan kata kunci pencarian:",
            placeholder="Contoh: ekonomi, politik, pendidikan...",
            help="Gunakan kata kunci untuk mencari artikel yang relevan"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        search_button = st.button("🔍 Cari", type="primary")
    
    # Advanced search options
    with st.expander("🔧 Opsi Pencarian Lanjutan"):
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            date_from = st.date_input("Dari tanggal:", value=None)
        with col_date2:
            date_to = st.date_input("Sampai tanggal:", value=None)
        
        sort_by = st.selectbox(
            "Urutkan berdasarkan:",
            ["Relevansi", "Tanggal (Terbaru)", "Tanggal (Terlama)"]
        )
    
    # Perform search
    if keyword.strip() or search_button:
        keyword = keyword.strip()
        
        if not keyword:
            st.warning("⚠️ Masukkan kata kunci untuk mencari.")
            return
        
        # Search dengan Elasticsearch
        if search_mode.startswith("🚀") and es_manager.is_connected():
            with st.spinner("🔍 Mencari dengan Elasticsearch..."):
                search_results = es_manager.search_articles(
                    query=keyword,
                    size=results_per_page
                )
            
            hasil = search_results.get('articles', [])
            total_found = search_results.get('total', 0)
            search_time = search_results.get('took', 0)
            
            # Display search info
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.metric("📊 Total Ditemukan", total_found)
            with col_info2:
                st.metric("⚡ Waktu Pencarian", f"{search_time}ms")
            with col_info3:
                st.metric("📄 Ditampilkan", len(hasil))
                
        else:
            # Fallback ke simple search
            with st.spinner("🔍 Mencari..."):
                hasil = [
                    b for b in berita 
                    if keyword.lower() in b.get("title", "").lower() or 
                       keyword.lower() in b.get("content", "").lower()
                ]
            
            st.metric("📊 Ditemukan", len(hasil))
        
        # Display results
        if hasil:
            st.markdown(f"### 📋 Hasil Pencarian untuk: `{keyword}`")
            st.markdown("---")
            
            for i, article in enumerate(hasil, 1):
                # Container untuk setiap artikel
                with st.container():
                    # Kolom untuk layout
                    col_main, col_date = st.columns([4, 1])
                    
                    with col_main:
                        # Title dengan highlighting
                        title = article.get("title", "Tanpa Judul")
                        if show_highlights and 'highlights' in article:
                            if 'title' in article['highlights']:
                                title = " ".join(article['highlights']['title'])
                        else:
                            title = highlight_text(title, keyword)
                        
                        st.markdown(f"**{i}. {title}**", unsafe_allow_html=True)
                        
                        # Content preview
                        if show_content_preview:
                            content = article.get("content", "")
                            if show_highlights and 'highlights' in article:
                                if 'content' in article['highlights']:
                                    content_preview = " ... ".join(article['highlights']['content'])
                                else:
                                    content_preview = potong_isi(content)
                            else:
                                content_preview = highlight_text(potong_isi(content), keyword)
                            
                            st.markdown(f"_{content_preview}_", unsafe_allow_html=True)
                        
                        # Score untuk Elasticsearch results
                        if 'score' in article:
                            st.caption(f"🎯 Relevance Score: {article['score']:.2f}")
                    
                    with col_date:
                        date_str = article.get("date", "")
                        formatted_date = format_date(date_str)
                        st.write(f"📅 {formatted_date}")
                    
                    # Separator
                    st.markdown("---")
            
            # Pagination info
            if len(hasil) >= results_per_page:
                st.info(f"📄 Menampilkan {len(hasil)} artikel pertama. Gunakan pengaturan di sidebar untuk melihat lebih banyak.")
                
        else:
            st.warning(f"😕 Tidak ditemukan artikel dengan kata kunci: `{keyword}`")
            
            # Suggestions
            if es_manager.is_connected():
                suggestions = es_manager.get_suggestions(keyword)
                if suggestions:
                    st.info("💡 Mungkin maksud Anda:")
                    for suggestion in suggestions:
                        if st.button(f"🔍 {suggestion}", key=f"sug_{suggestion}"):
                            st.experimental_rerun()
    
    else:
        # Default view - tampilkan informasi
        st.info("💡 Masukkan kata kunci di atas untuk memulai pencarian berita.")
        
        # Sample queries
        st.subheader("🎯 Contoh Pencarian:")
        sample_queries = ["ekonomi tambang", "pendidikan", "kesehatan", "politik", "lingkungan", "teknologi"]
        
        cols = st.columns(3)
        for i, query in enumerate(sample_queries):
            with cols[i % 3]:
                if st.button(f"🔍 {query}", key=f"sample_{query}"):
                    st.session_state['search_query'] = query
                    st.experimental_rerun()
        
        # System info
        with st.expander("ℹ️ Informasi Sistem"):
            st.write(f"📊 **Total Artikel**: {len(berita):,}")
            st.write(f"🗂️ **Sumber Data**: {DATA_PATH}")
            
            if berita:
                dates = [article.get('date', '') for article in berita if article.get('date')]
                if dates:
                    st.write(f"📅 **Rentang Tanggal**: {min(dates)[:10]} - {max(dates)[:10]}")
            
            st.write(f"🔧 **Mode Pencarian**: {search_mode}")

if __name__ == "__main__":
    main()
