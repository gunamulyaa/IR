"""
Enhanced Elasticsearch Configuration and Connection Management
"""
import os
import time
import logging
from typing import Optional, Dict, Any
from elasticsearch import Elasticsearch, ConnectionTimeout, ConnectionError
from elasticsearch.helpers import parallel_bulk
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElasticsearchManager:
    """Enhanced Elasticsearch connection and operations manager"""
    
    def __init__(self, 
                 host: str = None, 
                 username: str = None, 
                 password: str = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 retry_on_timeout: bool = True):
        
        self.host = host or os.getenv("ES_HOST", "http://localhost:9200")
        self.username = username or os.getenv("ES_USER")
        self.password = password or os.getenv("ES_PASS")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_on_timeout = retry_on_timeout
        
        self.client = self._create_client()
        
    def _create_client(self) -> Elasticsearch:
        """Create Elasticsearch client with enhanced configuration"""
        try:
            # Basic configuration
            config = {
                "hosts": [self.host],
                "timeout": self.timeout,
                "max_retries": self.max_retries,
                "retry_on_timeout": self.retry_on_timeout,
                "request_timeout": self.timeout,
                "http_compress": True,  # Enable compression
                "verify_certs": False,  # For development
            }
            
            # Add authentication if provided
            if self.username and self.password:
                config["basic_auth"] = (self.username, self.password)
            
            client = Elasticsearch(**config)
            
            # Test connection
            if not client.ping():
                raise ConnectionError("Failed to connect to Elasticsearch")
            
            logger.info(f"✅ Connected to Elasticsearch at {self.host}")
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to create Elasticsearch client: {str(e)}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch cluster health"""
        try:
            health = self.client.cluster.health()
            logger.info(f"Cluster status: {health['status']}")
            return health
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "red", "error": str(e)}
    
    def create_index_with_mapping(self, index_name: str, mapping: Dict[str, Any], force_recreate: bool = False):
        """Create index with enhanced mapping"""
        try:
            # Delete existing index if force recreate
            if force_recreate and self.client.indices.exists(index=index_name):
                self.client.indices.delete(index=index_name)
                logger.info(f"🗑️ Deleted existing index: {index_name}")
            
            # Create index if it doesn't exist
            if not self.client.indices.exists(index=index_name):
                self.client.indices.create(index=index_name, body=mapping)
                logger.info(f"✅ Created index: {index_name}")
            else:
                logger.info(f"ℹ️ Index {index_name} already exists")
                
        except Exception as e:
            logger.error(f"❌ Failed to create index {index_name}: {str(e)}")
            raise
    
    def bulk_index_with_progress(self, index_name: str, documents: list, chunk_size: int = 500):
        """Bulk index documents with progress tracking"""
        try:
            from tqdm import tqdm
            
            def doc_generator():
                for doc in documents:
                    yield {
                        "_index": index_name,
                        "_id": doc.get("passage_id", doc.get("id")),
                        "_source": doc
                    }
            
            # Use parallel bulk for better performance
            success_count = 0
            error_count = 0
            
            with tqdm(total=len(documents), desc="Indexing") as pbar:
                for success, info in parallel_bulk(
                    client=self.client,
                    actions=doc_generator(),
                    chunk_size=chunk_size,
                    thread_count=4,
                    max_chunk_bytes=10 * 1024 * 1024  # 10MB chunks
                ):
                    if success:
                        success_count += 1
                    else:
                        error_count += 1
                        logger.error(f"Failed to index document: {info}")
                    
                    pbar.update(1)
            
            logger.info(f"✅ Indexed {success_count} documents, {error_count} errors")
            return success_count, error_count
            
        except Exception as e:
            logger.error(f"❌ Bulk indexing failed: {str(e)}")
            raise
    
    def search_with_fallback(self, index_name: str, query: Dict[str, Any], size: int = 10):
        """Search with fallback mechanisms"""
        try:
            # Try the main query first
            response = self.client.search(
                index=index_name,
                body={"size": size, "query": query}
            )
            return response
            
        except Exception as e:
            logger.warning(f"Primary search failed: {str(e)}")
            
            # Fallback to simple match_all query
            try:
                fallback_query = {"match_all": {}}
                response = self.client.search(
                    index=index_name,
                    body={"size": size, "query": fallback_query}
                )
                logger.info("Used fallback query")
                return response
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {str(fallback_error)}")
                raise
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get comprehensive index statistics"""
        try:
            stats = self.client.indices.stats(index=index_name)
            doc_count = stats['indices'][index_name]['total']['docs']['count']
            size_bytes = stats['indices'][index_name]['total']['store']['size_in_bytes']
            
            return {
                "document_count": doc_count,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def close(self):
        """Close Elasticsearch connection"""
        try:
            self.client.close()
            logger.info("🔌 Elasticsearch connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")

# Enhanced index mapping with better field types and analyzers
def get_enhanced_mapping(vector_dims: int = 384) -> Dict[str, Any]:
    """Get enhanced mapping for news articles index"""
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "1s",
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
                        "stopwords": ["dan", "atau", "yang", "di", "ke", "dari", "untuk", "pada", "dengan", "adalah"]
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
                "doc_id": {
                    "type": "integer"
                },
                "passage_id": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text",
                    "analyzer": "indonesian_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                },
                "content": {
                    "type": "text",
                    "analyzer": "indonesian_analyzer",
                    "term_vector": "with_positions_offsets"
                },
                "content_vector": {
                    "type": "dense_vector",
                    "dims": vector_dims,
                    "index": True,
                    "similarity": "cosine"
                },
                "date": {
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"
                },
                "indexed_at": {
                    "type": "date"
                },
                "word_count": {
                    "type": "integer"
                },
                "source": {
                    "type": "keyword"
                }
            }
        }
    }
