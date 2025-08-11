import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElasticsearchManager:
    """
    Mengelola koneksi dan operasi Elasticsearch untuk sistem pencarian berita
    """
    
    def __init__(self):
        self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        self.port = int(os.getenv('ELASTICSEARCH_PORT', 9200))
        self.index_name = os.getenv('ELASTICSEARCH_INDEX', 'articles')
        self.username = os.getenv('ELASTICSEARCH_USERNAME', '')
        self.password = os.getenv('ELASTICSEARCH_PASSWORD', '')
        self.use_ssl = os.getenv('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true'
        
        self.client = self._create_client()
        
    def _create_client(self) -> Elasticsearch:
        """Membuat koneksi ke Elasticsearch"""
        try:
            # Konfigurasi dasar untuk development (tanpa SSL)
            client_config = {
                'hosts': [f"http://{self.host}:{self.port}"],
                'verify_certs': False,
                'ssl_show_warn': False,
                'request_timeout': 60,
                'max_retries': 3,
                'retry_on_timeout': True
            }
            
            # Tambahkan autentikasi jika diperlukan
            if self.username and self.password:
                client_config['basic_auth'] = (self.username, self.password)
            
            client = Elasticsearch(**client_config)
            
            # Test koneksi
            if client.ping():
                logger.info(f"Successfully connected to Elasticsearch at {self.host}:{self.port}")
                return client
            else:
                logger.error("Failed to connect to Elasticsearch")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Elasticsearch client: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Cek apakah koneksi ke Elasticsearch aktif"""
        try:
            return self.client and self.client.ping()
        except:
            return False
    
    def create_index(self) -> bool:
        """Membuat index dengan mapping yang optimal untuk artikel berita"""
        try:
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"Index {self.index_name} already exists")
                return True
            
            # Mapping untuk struktur artikel berita
            mapping = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "indonesian_analyzer": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "stop_indonesian",
                                    "stemmer_indonesian"
                                ]
                            }
                        },
                        "filter": {
                            "stop_indonesian": {
                                "type": "stop",
                                "stopwords": ["yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada", "adalah", "ini", "itu", "atau", "juga", "akan", "telah", "dapat", "bisa", "sudah", "belum", "tidak", "ya", "iya"]
                            },
                            "stemmer_indonesian": {
                                "type": "stemmer",
                                "language": "indonesian"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "title": {
                            "type": "text",
                            "analyzer": "indonesian_analyzer",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                },
                                "suggest": {
                                    "type": "completion"
                                }
                            }
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "indonesian_analyzer"
                        },
                        "date": {
                            "type": "date",
                            "format": "yyyy-MM-dd HH:mm:ss"
                        },
                        "created_at": {
                            "type": "date"
                        }
                    }
                }
            }
            
            self.client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"Index {self.index_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    def delete_index(self) -> bool:
        """Menghapus index"""
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"Index {self.index_name} deleted successfully")
                return True
            else:
                logger.info(f"Index {self.index_name} does not exist")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False
    
    def index_articles(self, articles: List[Dict[str, Any]]) -> bool:
        """Mengindex artikel-artikel ke Elasticsearch"""
        try:
            if not self.client:
                logger.error("Elasticsearch client not available")
                return False
            
            # Prepare bulk indexing
            actions = []
            for i, article in enumerate(articles):
                # Pastikan semua field yang diperlukan ada
                if not all(key in article for key in ['title', 'content', 'date']):
                    logger.warning(f"Article {i} missing required fields, skipping...")
                    continue
                
                action = {
                    "_index": self.index_name,
                    "_id": i,
                    "_source": {
                        "title": article.get('title', ''),
                        "content": article.get('content', ''),
                        "date": article.get('date', ''),
                        "created_at": datetime.now().isoformat()
                    }
                }
                actions.append(action)
            
            # Bulk index dengan batch processing
            from elasticsearch.helpers import bulk
            
            success_count, failed_count = bulk(
                self.client,
                actions,
                chunk_size=100,
                request_timeout=60
            )
            
            logger.info(f"Successfully indexed {len(actions)} articles")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing articles: {e}")
            return False
    
    def search_articles(self, query: str, size: int = 10, from_: int = 0) -> Dict[str, Any]:
        """
        Mencari artikel dengan query yang canggih
        
        Args:
            query: Query pencarian
            size: Jumlah hasil yang dikembalikan
            from_: Offset untuk pagination
            
        Returns:
            Dictionary berisi hasil pencarian dan metadata
        """
        try:
            if not self.client:
                return {"articles": [], "total": 0, "error": "Elasticsearch not available"}
            
            # Query yang lebih canggih dengan multi-field search dan boosting
            search_body = {
                "size": size,
                "from": from_,
                "query": {
                    "bool": {
                        "should": [
                            # Exact match pada title (boost tinggi)
                            {
                                "match_phrase": {
                                    "title": {
                                        "query": query,
                                        "boost": 3.0
                                    }
                                }
                            },
                            # Fuzzy match pada title (boost sedang)
                            {
                                "match": {
                                    "title": {
                                        "query": query,
                                        "boost": 2.0,
                                        "fuzziness": "AUTO"
                                    }
                                }
                            },
                            # Match pada content (boost rendah)
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "boost": 1.0
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "highlight": {
                    "fields": {
                        "title": {
                            "pre_tags": ["<mark>"],
                            "post_tags": ["</mark>"]
                        },
                        "content": {
                            "pre_tags": ["<mark>"],
                            "post_tags": ["</mark>"],
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                },
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"date": {"order": "desc"}}
                ]
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            # Process hasil
            articles = []
            for hit in response['hits']['hits']:
                article = hit['_source'].copy()
                article['score'] = hit['_score']
                
                # Tambahkan highlight jika ada
                if 'highlight' in hit:
                    article['highlights'] = hit['highlight']
                
                articles.append(article)
            
            return {
                "articles": articles,
                "total": response['hits']['total']['value'],
                "max_score": response['hits']['max_score'],
                "took": response['took']
            }
            
        except Exception as e:
            logger.error(f"Error searching articles: {e}")
            return {"articles": [], "total": 0, "error": str(e)}
    
    def get_suggestions(self, query: str, size: int = 5) -> List[str]:
        """Mendapatkan saran kata kunci untuk autocomplete"""
        try:
            if not self.client or len(query.strip()) < 2:
                return []
            
            search_body = {
                "suggest": {
                    "title_suggest": {
                        "prefix": query,
                        "completion": {
                            "field": "title.suggest",
                            "size": size
                        }
                    }
                }
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            suggestions = []
            for suggestion in response['suggest']['title_suggest'][0]['options']:
                suggestions.append(suggestion['text'])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    def get_article_stats(self) -> Dict[str, Any]:
        """Mendapatkan statistik artikel"""
        try:
            if not self.client:
                return {}
            
            # Total count
            count_response = self.client.count(index=self.index_name)
            total_articles = count_response['count']
            
            # Date range aggregation
            agg_body = {
                "size": 0,
                "aggs": {
                    "date_range": {
                        "stats": {
                            "field": "date"
                        }
                    },
                    "articles_per_month": {
                        "date_histogram": {
                            "field": "date",
                            "calendar_interval": "month",
                            "format": "yyyy-MM"
                        }
                    }
                }
            }
            
            agg_response = self.client.search(index=self.index_name, body=agg_body)
            
            return {
                "total_articles": total_articles,
                "date_stats": agg_response['aggregations']['date_range'],
                "monthly_distribution": agg_response['aggregations']['articles_per_month']['buckets']
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

def load_articles_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load artikel dari file JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        
        logger.info(f"Loaded {len(articles)} articles from {file_path}")
        return articles
        
    except Exception as e:
        logger.error(f"Error loading articles from {file_path}: {e}")
        return []

def main():
    """Fungsi utama untuk testing dan setup"""
    
    # Initialize Elasticsearch manager
    es_manager = ElasticsearchManager()
    
    if not es_manager.is_connected():
        print("❌ Failed to connect to Elasticsearch. Please make sure Elasticsearch is running.")
        print("💡 To install and run Elasticsearch locally:")
        print("   1. Download from: https://www.elastic.co/downloads/elasticsearch")
        print("   2. Extract and run: bin/elasticsearch (Linux/Mac) or bin\\elasticsearch.bat (Windows)")
        print("   3. Check if running: curl http://localhost:9200")
        return
    
    print("✅ Connected to Elasticsearch successfully!")
    
    # Load articles
    data_path = os.path.join("Data", "combined_articles.json")
    articles = load_articles_from_json(data_path)
    
    if not articles:
        print("❌ No articles found!")
        return
    
    print(f"📰 Found {len(articles)} articles")
    
    # Setup index
    print("🔧 Setting up Elasticsearch index...")
    es_manager.delete_index()  # Clean start
    
    if es_manager.create_index():
        print("✅ Index created successfully!")
    else:
        print("❌ Failed to create index!")
        return
    
    # Index articles
    print("📥 Indexing articles...")
    if es_manager.index_articles(articles):
        print("✅ Articles indexed successfully!")
    else:
        print("❌ Failed to index articles!")
        return
    
    # Test search
    print("\n🔍 Testing search functionality...")
    test_queries = ["ekonomi", "politik", "pendidikan", "kesehatan"]
    
    for query in test_queries:
        results = es_manager.search_articles(query, size=3)
        print(f"\n📊 Query: '{query}' - Found {results['total']} articles")
        
        for i, article in enumerate(results['articles'][:2], 1):
            print(f"   {i}. {article['title'][:80]}...")
    
    # Show stats
    stats = es_manager.get_article_stats()
    if stats:
        print(f"\n📈 Statistics:")
        print(f"   Total articles: {stats.get('total_articles', 0)}")
    
    print("\n🎉 Setup completed! You can now run the Streamlit app with enhanced search.")

if __name__ == "__main__":
    main()
