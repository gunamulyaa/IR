import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from .query_preprocessing import clean_query
from .elasticsearch_config import ElasticsearchManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDEX_NAME = "news_passages_v2"  # Updated to use new index
MODEL_NAME = "all-MiniLM-L6-v2"

class EnhancedRetrieval:
    """Enhanced retrieval system with multiple search strategies"""
    
    def __init__(self, es_manager: ElasticsearchManager = None):
        self.es_manager = es_manager or ElasticsearchManager()
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load sentence transformer model with caching"""
        try:
            if self.model is None:
                logger.info(f"🤖 Loading model: {MODEL_NAME}")
                self.model = SentenceTransformer(MODEL_NAME)
                logger.info("✅ Model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {str(e)}")
            raise
    
    def hybrid_search(self, 
                     query: str, 
                     k: int = 5,
                     semantic_weight: float = 0.7,
                     date_filter: Optional[Dict[str, str]] = None,
                     min_score: float = 0.5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword search
        
        Args:
            query: Search query
            k: Number of results to return
            semantic_weight: Weight for semantic search (0.0 to 1.0)
            date_filter: Date range filter {"from": "2024-01-01", "to": "2024-12-31"}
            min_score: Minimum similarity score threshold
        """
        try:
            # Clean and process query
            clean_q = clean_query(query)
            if not clean_q:
                return []
            
            # Generate query vector
            q_vec = self.model.encode(clean_q, normalize_embeddings=True).tolist()
            
            # Build hybrid query
            hybrid_query = self._build_hybrid_query(
                query_text=clean_q,
                query_vector=q_vec,
                semantic_weight=semantic_weight,
                date_filter=date_filter
            )
            
            # Execute search
            response = self.es_manager.search_with_fallback(
                index_name=INDEX_NAME,
                query=hybrid_query,
                size=k * 2  # Get more results to filter by score
            )
            
            # Process and filter results
            results = self._process_results(response, min_score, k)
            
            logger.info(f"🔍 Found {len(results)} results for query: '{query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {str(e)}")
            return []
    
    def _build_hybrid_query(self, 
                           query_text: str, 
                           query_vector: List[float],
                           semantic_weight: float,
                           date_filter: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Build hybrid query combining semantic and keyword search"""
        
        # Semantic search query
        semantic_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                    "params": {"query_vector": query_vector}
                },
                "boost": semantic_weight
            }
        }
        
        # Keyword search queries
        keyword_queries = [
            {
                "multi_match": {
                    "query": query_text,
                    "fields": ["title^2", "content"],
                    "type": "best_fields",
                    "boost": 1.0 - semantic_weight
                }
            },
            {
                "match_phrase": {
                    "content": {
                        "query": query_text,
                        "boost": 0.5 * (1.0 - semantic_weight)
                    }
                }
            }
        ]
        
        # Combine queries
        combined_query = {
            "bool": {
                "should": [semantic_query] + keyword_queries,
                "minimum_should_match": 1
            }
        }
        
        # Add date filter if provided
        if date_filter:
            combined_query["bool"]["filter"] = [
                {
                    "range": {
                        "date": {
                            "gte": date_filter.get("from"),
                            "lte": date_filter.get("to")
                        }
                    }
                }
            ]
        
        return combined_query
    
    def semantic_search_only(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Pure semantic search using only vector similarity"""
        try:
            clean_q = clean_query(query)
            q_vec = self.model.encode(clean_q, normalize_embeddings=True).tolist()
            
            script_query = {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                        "params": {"query_vector": q_vec}
                    }
                }
            }
            
            response = self.es_manager.search_with_fallback(
                index_name=INDEX_NAME,
                query=script_query,
                size=k
            )
            
            return self._process_results(response, min_score=0.0, max_results=k)
            
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {str(e)}")
            return []
    
    def keyword_search_only(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Pure keyword search using text matching"""
        try:
            clean_q = clean_query(query)
            
            keyword_query = {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": clean_q,
                                "fields": ["title^3", "content"],
                                "type": "best_fields"
                            }
                        },
                        {
                            "match_phrase": {
                                "content": {
                                    "query": clean_q,
                                    "boost": 0.5
                                }
                            }
                        }
                    ]
                }
            }
            
            response = self.es_manager.search_with_fallback(
                index_name=INDEX_NAME,
                query=keyword_query,
                size=k
            )
            
            return self._process_results(response, min_score=0.0, max_results=k)
            
        except Exception as e:
            logger.error(f"❌ Keyword search failed: {str(e)}")
            return []
    
    def search_by_date_range(self, 
                           query: str, 
                           start_date: str, 
                           end_date: str, 
                           k: int = 5) -> List[Dict[str, Any]]:
        """Search within specific date range"""
        date_filter = {"from": start_date, "to": end_date}
        return self.hybrid_search(query, k=k, date_filter=date_filter)
    
    def get_similar_articles(self, article_id: str, k: int = 5) -> List[Dict[str, Any]]:
        """Find articles similar to a given article"""
        try:
            # Get the source article
            source_doc = self.es_manager.client.get(index=INDEX_NAME, id=article_id)
            source_vector = source_doc["_source"].get("content_vector")
            
            if not source_vector:
                logger.error("Source article has no content vector")
                return []
            
            # Find similar articles
            similar_query = {
                "script_score": {
                    "query": {
                        "bool": {
                            "must_not": [
                                {"term": {"passage_id": article_id}}
                            ]
                        }
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                        "params": {"query_vector": source_vector}
                    }
                }
            }
            
            response = self.es_manager.search_with_fallback(
                index_name=INDEX_NAME,
                query=similar_query,
                size=k
            )
            
            return self._process_results(response, min_score=1.0, max_results=k)
            
        except Exception as e:
            logger.error(f"❌ Similar articles search failed: {str(e)}")
            return []
    
    def _process_results(self, 
                        response: Dict[str, Any], 
                        min_score: float, 
                        max_results: int) -> List[Dict[str, Any]]:
        """Process and format search results"""
        results = []
        
        for hit in response.get("hits", {}).get("hits", []):
            score = hit["_score"]
            
            # Filter by minimum score
            if score < min_score:
                continue
            
            source = hit["_source"]
            result = {
                "id": hit["_id"],
                "score": round(score, 4),
                "title": source.get("title", "No Title"),
                "content": source.get("content", ""),
                "date": source.get("date", ""),
                "word_count": source.get("word_count", 0),
                "passage_id": source.get("passage_id", "")
            }
            
            results.append(result)
            
            # Limit results
            if len(results) >= max_results:
                break
        
        return results

# Global instance for backward compatibility
_retrieval_instance = None

def get_retrieval_instance():
    """Get or create global retrieval instance"""
    global _retrieval_instance
    if _retrieval_instance is None:
        _retrieval_instance = EnhancedRetrieval()
    return _retrieval_instance

# Legacy function for backward compatibility
def run_retrieval(es, query: str, k: int = 5) -> List[Dict[str, Any]]:
    """Legacy retrieval function for backward compatibility"""
    try:
        retrieval = get_retrieval_instance()
        return retrieval.hybrid_search(query, k=k)
    except Exception as e:
        logger.error(f"Legacy retrieval failed: {str(e)}")
        # Fallback to simple semantic search
        try:
            retrieval = get_retrieval_instance()
            return retrieval.semantic_search_only(query, k=k)
        except Exception as e2:
            logger.error(f"Fallback retrieval also failed: {str(e2)}")
            return []
