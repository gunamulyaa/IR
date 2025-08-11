# 🎯 Quick Start Guide

## Untuk Menjalankan Aplikasi SEKARANG

### Option 1: Quick Start (Termudah)
```bash
python quick_start.py
```

### Option 2: Manual
```bash
# Pastikan di virtual environment
.venv\Scripts\activate

# Install requirements jika belum
pip install streamlit pandas

# Jalankan aplikasi
streamlit run app.py
```

### Option 3: Windows Batch Files
```bash
# Install requirements
install.bat

# Jalankan aplikasi
run.bat
```

## Untuk Menggunakan Elasticsearch (Advanced)

### 1. Install Elasticsearch
```bash
# Docker (Recommended)
docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.1

# Manual download dari: https://www.elastic.co/downloads/elasticsearch
```

### 2. Setup Data
```bash
python setup_elasticsearch.py --setup
```

### 3. Jalankan Enhanced App
```bash
streamlit run app_elasticsearch.py
```

## Troubleshooting

### Jika ada error "module not found":
```bash
pip install -r requirements.txt
```

### Jika Elasticsearch tidak konek:
- App akan otomatis fallback ke mode simple
- Install Elasticsearch untuk fitur advanced

## Fitur yang Tersedia

### Mode Simple (app.py):
- ✅ Pencarian dasar di 532 artikel
- ✅ Interface web Streamlit
- ✅ Highlighting sederhana

### Mode Enhanced (app_elasticsearch.py):
- ✅ Semua fitur simple +
- ✅ Search 10x lebih cepat dan akurat
- ✅ Fuzzy matching (toleransi typo)
- ✅ Relevance scoring
- ✅ Autocomplete suggestions
- ✅ Advanced highlighting
- ✅ Real-time statistics

---

**🚀 Start dengan menjalankan: `python quick_start.py`**
