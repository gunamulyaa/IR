"""
🚀 Quick Start Guide untuk IR System dengan Elasticsearch
========================================================

Script ini akan membantu Anda menjalankan sistem dengan atau tanpa Elasticsearch.
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           📰 Information Retrieval System                     ║
    ║                  dengan Elasticsearch                        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_requirements():
    """Check jika semua requirements sudah terpenuhi"""
    print("🔍 Checking requirements...")
    
    # Check Python packages
    required_packages = ['streamlit', 'elasticsearch', 'pandas', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    # Check data file
    data_path = Path("Data/combined_articles.json")
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"   ✅ Data file found ({len(articles)} articles)")
    else:
        print(f"   ❌ Data file not found: {data_path}")
        return False
    
    return True

def check_elasticsearch():
    """Check jika Elasticsearch berjalan"""
    print("\n🔍 Checking Elasticsearch...")
    
    try:
        from elasticsearch_manager import ElasticsearchManager
        es = ElasticsearchManager()
        
        if es.is_connected():
            print("   ✅ Elasticsearch is running")
            
            # Get some stats
            try:
                info = es.client.info()
                print(f"   📊 Version: {info['version']['number']}")
                print(f"   📊 Cluster: {info['cluster_name']}")
            except:
                pass
                
            return True
        else:
            print("   ❌ Elasticsearch is not running")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking Elasticsearch: {e}")
        return False

def show_elasticsearch_options():
    """Tampilkan opsi untuk menjalankan Elasticsearch"""
    print("\n💡 Cara menjalankan Elasticsearch:")
    print("\n1️⃣ Menggunakan Docker (Recommended):")
    print("   docker run -d --name elasticsearch -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.1")
    
    print("\n2️⃣ Download Manual:")
    print("   • Download: https://www.elastic.co/downloads/elasticsearch")
    print("   • Extract dan jalankan: bin/elasticsearch")
    
    print("\n3️⃣ Package Manager:")
    print("   • Windows: Download dan install dari website")
    print("   • macOS: brew install elasticsearch && brew services start elasticsearch")
    print("   • Ubuntu: sudo apt install elasticsearch && sudo systemctl start elasticsearch")
    
    print("\n🔗 Setelah install, cek di: http://localhost:9200")

def run_simple_app():
    """Jalankan aplikasi sederhana tanpa Elasticsearch"""
    print("\n🚀 Starting Simple Search App...")
    print("   📱 App will open in browser automatically")
    print("   🛑 Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n👋 App stopped")

def run_elasticsearch_app():
    """Jalankan aplikasi dengan Elasticsearch"""
    print("\n🚀 Starting Enhanced Search App with Elasticsearch...")
    print("   📱 App will open in browser automatically")
    print("   🛑 Press Ctrl+C to stop")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app_elasticsearch.py",
            "--server.port", "8501",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n👋 App stopped")

def setup_elasticsearch_data():
    """Setup data di Elasticsearch"""
    print("\n🔧 Setting up Elasticsearch data...")
    
    try:
        from setup_elasticsearch import setup_elasticsearch
        if setup_elasticsearch():
            print("✅ Elasticsearch setup completed!")
            return True
        else:
            print("❌ Elasticsearch setup failed!")
            return False
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        return False

def main():
    """Main function"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed!")
        print("Please install missing requirements and try again.")
        return
    
    print("✅ All requirements satisfied!")
    
    # Check Elasticsearch
    es_available = check_elasticsearch()
    
    print("\n" + "="*60)
    
    if es_available:
        print("🎉 Elasticsearch detected!")
        
        while True:
            print("\nWhat would you like to do?")
            print("1️⃣ Setup Elasticsearch data (recommended for first time)")
            print("2️⃣ Run Enhanced App with Elasticsearch")
            print("3️⃣ Run Simple App (without Elasticsearch)")
            print("4️⃣ Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                if setup_elasticsearch_data():
                    print("\n🎯 Now you can run the enhanced app!")
                else:
                    print("\n⚠️ Setup failed, but you can still try running the app")
                    
            elif choice == "2":
                run_elasticsearch_app()
                break
                
            elif choice == "3":
                run_simple_app()
                break
                
            elif choice == "4":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice, please try again")
    
    else:
        print("⚠️ Elasticsearch not available")
        show_elasticsearch_options()
        
        while True:
            print("\nWhat would you like to do?")
            print("1️⃣ Run Simple App (without Elasticsearch)")
            print("2️⃣ Check Elasticsearch again")
            print("3️⃣ Exit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == "1":
                run_simple_app()
                break
                
            elif choice == "2":
                if check_elasticsearch():
                    print("✅ Great! Elasticsearch is now running!")
                    print("Restarting script with Elasticsearch support...")
                    time.sleep(1)
                    main()  # Restart with ES support
                    return
                else:
                    print("❌ Still no Elasticsearch detected")
                    
            elif choice == "3":
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Script interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your setup and try again")
