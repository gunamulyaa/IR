"""
Setup Script untuk Elasticsearch Information Retrieval System

Script ini akan:
1. Memeriksa koneksi Elasticsearch
2. Mengatur index dan mapping
3. Mengindeks artikel dari file JSON
4. Menjalankan testing dasar
"""

import os
import sys
import time
import subprocess
from elasticsearch_manager import ElasticsearchManager, load_articles_from_json

def check_elasticsearch_running():
    """Cek apakah Elasticsearch sedang berjalan"""
    es = ElasticsearchManager()
    return es.is_connected()

def setup_elasticsearch():
    """Setup lengkap Elasticsearch untuk sistem IR"""
    print("🚀 === SETUP ELASTICSEARCH IR SYSTEM ===\n")
    
    # 1. Cek koneksi Elasticsearch
    print("1️⃣ Checking Elasticsearch connection...")
    if not check_elasticsearch_running():
        print("❌ Elasticsearch tidak berjalan!")
        print("\n💡 Cara menjalankan Elasticsearch:")
        print("   • Docker: docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.1")
        print("   • Manual: Download dari https://www.elastic.co/downloads/elasticsearch")
        print("   • Homebrew: brew install elasticsearch && brew services start elasticsearch")
        print("   • Ubuntu: sudo systemctl start elasticsearch")
        return False
    
    print("✅ Elasticsearch connected successfully!")
    
    # 2. Load artikel
    print("\n2️⃣ Loading articles from JSON...")
    data_path = os.path.join("Data", "combined_articles.json")
    articles = load_articles_from_json(data_path)
    
    if not articles:
        print("❌ No articles found!")
        return False
    
    print(f"✅ Loaded {len(articles)} articles")
    
    # 3. Setup Elasticsearch
    print("\n3️⃣ Setting up Elasticsearch index...")
    es_manager = ElasticsearchManager()
    
    # Hapus index lama jika ada
    print("   🗑️ Cleaning old index...")
    es_manager.delete_index()
    
    # Buat index baru
    print("   🔧 Creating new index with optimized mapping...")
    if not es_manager.create_index():
        print("❌ Failed to create index!")
        return False
    
    print("✅ Index created successfully!")
    
    # 4. Index artikel
    print("\n4️⃣ Indexing articles...")
    print("   📥 This may take a moment...")
    
    start_time = time.time()
    if not es_manager.index_articles(articles):
        print("❌ Failed to index articles!")
        return False
    
    index_time = time.time() - start_time
    print(f"✅ Articles indexed successfully in {index_time:.2f} seconds!")
    
    # 5. Refresh index
    print("\n5️⃣ Refreshing index...")
    es_manager.client.indices.refresh(index=es_manager.index_name)
    print("✅ Index refreshed!")
    
    # 6. Testing pencarian
    print("\n6️⃣ Testing search functionality...")
    test_queries = ["ekonomi", "politik", "kesehatan", "pendidikan", "teknologi"]
    
    for query in test_queries[:3]:  # Test 3 queries pertama
        print(f"   🔍 Testing query: '{query}'")
        results = es_manager.search_articles(query, size=3)
        
        if results['total'] > 0:
            print(f"      ✅ Found {results['total']} articles (showing {len(results['articles'])})")
            for i, article in enumerate(results['articles'][:2], 1):
                title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
                print(f"         {i}. {title}")
        else:
            print(f"      ⚠️ No results found")
    
    # 7. Statistics
    print("\n7️⃣ Getting system statistics...")
    stats = es_manager.get_article_stats()
    
    if stats:
        print(f"   📊 Total indexed articles: {stats.get('total_articles', 0)}")
        if 'date_stats' in stats and stats['date_stats']:
            date_stats = stats['date_stats']
            if 'min_as_string' in date_stats:
                print(f"   📅 Oldest article: {date_stats['min_as_string'][:10]}")
            if 'max_as_string' in date_stats:
                print(f"   📅 Newest article: {date_stats['max_as_string'][:10]}")
    
    print("\n🎉 === SETUP COMPLETED SUCCESSFULLY! ===")
    print("\n📝 Next steps:")
    print("   • Run Streamlit app: streamlit run app_elasticsearch.py")
    print("   • Or run original app: streamlit run app.py")
    print("   • Access Elasticsearch directly: http://localhost:9200")
    
    return True

def quick_test():
    """Quick test untuk verifikasi sistem"""
    print("🧪 === QUICK SYSTEM TEST ===\n")
    
    es_manager = ElasticsearchManager()
    
    if not es_manager.is_connected():
        print("❌ Elasticsearch not connected!")
        return False
    
    # Test search
    test_query = "ekonomi"
    print(f"🔍 Testing search with query: '{test_query}'")
    
    results = es_manager.search_articles(test_query, size=5)
    
    if results['total'] > 0:
        print(f"✅ Search working! Found {results['total']} articles")
        print(f"   Search took: {results.get('took', 0)}ms")
        print(f"   Max score: {results.get('max_score', 0):.2f}")
        
        print("\n📰 Sample results:")
        for i, article in enumerate(results['articles'][:3], 1):
            print(f"   {i}. {article['title'][:80]}...")
            print(f"      Score: {article.get('score', 0):.2f}")
    else:
        print("❌ No search results found!")
        return False
    
    print("\n✅ System test passed!")
    return True

def run_streamlit():
    """Menjalankan aplikasi Streamlit"""
    print("🌟 Starting Streamlit application...")
    
    # Cek apakah Elasticsearch berjalan
    if not check_elasticsearch_running():
        print("⚠️ Elasticsearch not running. Starting app with fallback mode...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    else:
        print("✅ Elasticsearch detected. Starting enhanced app...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app_elasticsearch.py"])

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Elasticsearch IR System Setup")
    parser.add_argument("--setup", action="store_true", help="Run full setup")
    parser.add_argument("--test", action="store_true", help="Run quick test")
    parser.add_argument("--run", action="store_true", help="Run Streamlit app")
    parser.add_argument("--all", action="store_true", help="Setup, test, and run")
    
    args = parser.parse_args()
    
    if args.setup or args.all:
        if setup_elasticsearch():
            print("✅ Setup completed successfully!")
        else:
            print("❌ Setup failed!")
            sys.exit(1)
    
    if args.test or args.all:
        print("\n" + "="*50)
        if quick_test():
            print("✅ Test completed successfully!")
        else:
            print("❌ Test failed!")
            sys.exit(1)
    
    if args.run or args.all:
        print("\n" + "="*50)
        run_streamlit()
    
    if not any([args.setup, args.test, args.run, args.all]):
        print("🤖 Elasticsearch IR System Setup")
        print("\nAvailable commands:")
        print("  python setup_elasticsearch.py --setup    # Setup Elasticsearch")
        print("  python setup_elasticsearch.py --test     # Test system")
        print("  python setup_elasticsearch.py --run      # Run Streamlit app")
        print("  python setup_elasticsearch.py --all      # Do everything")
        print("\nMake sure Elasticsearch is running on localhost:9200")
