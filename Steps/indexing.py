import json
import logging
from datetime import datetime
from elasticsearch import Elasticsearch
from .elasticsearch_config import ElasticsearchManager, get_enhanced_mapping

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INDEX_NAME = "news_passages_v2"  # Updated version

def enhance_documents(data: list) -> list:
    """Enhance documents with additional metadata"""
    enhanced_docs = []
    
    for doc in data:
        # Add metadata
        doc["indexed_at"] = datetime.now().isoformat()
        doc["word_count"] = len(doc.get("content", "").split())
        doc["source"] = "combined_articles"
        
        # Ensure date field exists and is properly formatted
        if "date" not in doc and "date" in doc:
            doc["date"] = doc.get("date")
        
        enhanced_docs.append(doc)
    
    return enhanced_docs

def create_enhanced_index(es_manager: ElasticsearchManager, vector_dims: int):
    """Create index with enhanced mapping"""
    mapping = get_enhanced_mapping(vector_dims)
    es_manager.create_index_with_mapping(
        index_name=INDEX_NAME, 
        mapping=mapping, 
        force_recreate=True
    )

def run_indexing(es, input_path: str) -> int:
    """
    Enhanced indexing with better error handling and monitoring
    
    Args:
        es: Elasticsearch client or ElasticsearchManager
        input_path: Path to embedded data JSON file
    
    Returns:
        Number of successfully indexed documents
    """
    try:
        # Load and validate data
        logger.info(f"📂 Loading data from {input_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data:
            raise ValueError("No data found in input file")
        
        logger.info(f"📊 Loaded {len(data)} documents")
        
        # Initialize ElasticsearchManager if needed
        if not isinstance(es, ElasticsearchManager):
            es_manager = ElasticsearchManager()
        else:
            es_manager = es
        
        # Health check
        health = es_manager.health_check()
        if health.get("status") == "red":
            logger.warning("⚠️ Elasticsearch cluster health is RED")
        
        # Validate vector dimensions
        if not data[0].get("content_vector"):
            raise ValueError("Documents don't contain content_vector field")
        
        vector_dims = len(data[0]["content_vector"])
        logger.info(f"🔢 Vector dimensions: {vector_dims}")
        
        # Create enhanced index
        create_enhanced_index(es_manager, vector_dims)
        
        # Enhance documents with metadata
        enhanced_data = enhance_documents(data)
        
        # Bulk index with progress tracking
        success_count, error_count = es_manager.bulk_index_with_progress(
            index_name=INDEX_NAME,
            documents=enhanced_data,
            chunk_size=500
        )
        
        # Refresh index to make documents searchable immediately
        es_manager.client.indices.refresh(index=INDEX_NAME)
        
        # Get final statistics
        stats = es_manager.get_index_stats(INDEX_NAME)
        logger.info(f"📈 Index stats: {stats}")
        
        logger.info(f"✅ Indexing completed successfully!")
        logger.info(f"📊 Success: {success_count}, Errors: {error_count}")
        
        return success_count
        
    except FileNotFoundError:
        logger.error(f"❌ Input file not found: {input_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in input file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ Indexing failed: {str(e)}")
        raise

def get_index_info(es_manager: ElasticsearchManager) -> dict:
    """Get comprehensive index information"""
    try:
        stats = es_manager.get_index_stats(INDEX_NAME)
        mapping = es_manager.client.indices.get_mapping(index=INDEX_NAME)
        settings = es_manager.client.indices.get_settings(index=INDEX_NAME)
        
        return {
            "index_name": INDEX_NAME,
            "stats": stats,
            "mapping_fields": list(mapping[INDEX_NAME]["mappings"]["properties"].keys()),
            "settings": settings[INDEX_NAME]["settings"]
        }
    except Exception as e:
        logger.error(f"Failed to get index info: {str(e)}")
        return {"error": str(e)}

# Legacy function for backward compatibility
def run_indexing_legacy(es, input_path):
    """Legacy indexing function for backward compatibility"""
    return run_indexing(es, input_path)
