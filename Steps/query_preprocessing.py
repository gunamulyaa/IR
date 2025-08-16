import re
import logging
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_query(query: str) -> str:
    """
    Enhanced query cleaning and preprocessing
    
    Args:
        query: Raw query string
    
    Returns:
        Cleaned query string
    """
    if not query:
        return ""
    
    # Remove URLs
    query = re.sub(r"https?://\S+|www\.\S+", "", query)
    
    # Remove email addresses
    query = re.sub(r"\S+@\S+", "", query)
    
    # Remove excessive whitespace
    query = re.sub(r"\s+", " ", query).strip()
    
    # Remove special characters but keep meaningful punctuation
    query = re.sub(r"[^\w\s\-\.\,\!\?\;\:]", " ", query)
    
    # Normalize quotes and dashes
    query = re.sub(r"[""''`]", '"', query)
    query = re.sub(r"[–—]", "-", query)
    
    # Convert to lowercase
    query = query.lower()
    
    return query

def expand_query(query: str) -> List[str]:
    """
    Generate query expansions for better search coverage
    
    Args:
        query: Original query
    
    Returns:
        List of expanded queries
    """
    expanded_queries = [query]
    
    # Indonesian synonyms mapping
    synonyms = {
        "teknologi": ["teknologi", "teknik", "inovasi", "digital"],
        "ekonomi": ["ekonomi", "keuangan", "bisnis", "perdagangan"],
        "politik": ["politik", "pemerintah", "kebijakan", "negara"],
        "pendidikan": ["pendidikan", "sekolah", "universitas", "belajar"],
        "kesehatan": ["kesehatan", "medis", "rumah sakit", "dokter"],
        "lingkungan": ["lingkungan", "alam", "ekologi", "hijau"],
        "energy": ["energi", "listrik", "power", "tenaga"],
        "climate": ["iklim", "cuaca", "lingkungan", "global warming"]
    }
    
    # Add synonym expansions
    words = query.split()
    for word in words:
        if word in synonyms:
            for synonym in synonyms[word]:
                if synonym != word:
                    expanded_query = query.replace(word, synonym)
                    expanded_queries.append(expanded_query)
    
    return list(set(expanded_queries))  # Remove duplicates

def extract_search_terms(query: str) -> Dict[str, Any]:
    """
    Extract different types of search terms from query
    
    Args:
        query: Input query
    
    Returns:
        Dictionary with extracted terms
    """
    # Clean query first
    clean_q = clean_query(query)
    
    # Extract quoted phrases
    quoted_phrases = re.findall(r'"([^"]*)"', query)
    
    # Extract dates (basic patterns)
    date_patterns = [
        r'\b\d{4}\b',  # Year
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # Date formats
        r'\b(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember)\b'  # Indonesian months
    ]
    
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, clean_q, re.IGNORECASE))
    
    # Extract entities (basic NER)
    # Look for capitalized words that might be names, places, organizations
    entities = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', query)
    
    # Extract keywords (remove stop words)
    indonesian_stopwords = {
        "dan", "atau", "yang", "di", "ke", "dari", "untuk", "pada", "dengan", 
        "adalah", "ini", "itu", "tidak", "ada", "akan", "telah", "sudah",
        "dapat", "bisa", "harus", "juga", "saja", "hanya", "masih", "lebih"
    }
    
    words = clean_q.split()
    keywords = [word for word in words if len(word) > 2 and word not in indonesian_stopwords]
    
    return {
        "original_query": query,
        "cleaned_query": clean_q,
        "quoted_phrases": quoted_phrases,
        "dates": dates,
        "entities": entities,
        "keywords": keywords,
        "expanded_queries": expand_query(clean_q)
    }

def validate_query(query: str) -> Dict[str, Any]:
    """
    Validate query and provide suggestions
    
    Args:
        query: Input query
    
    Returns:
        Validation result with suggestions
    """
    if not query or not query.strip():
        return {
            "valid": False,
            "error": "Query is empty",
            "suggestions": ["Please enter a search term"]
        }
    
    clean_q = clean_query(query)
    
    if len(clean_q) < 2:
        return {
            "valid": False,
            "error": "Query too short",
            "suggestions": ["Please enter at least 2 characters"]
        }
    
    if len(clean_q) > 500:
        return {
            "valid": False,
            "error": "Query too long",
            "suggestions": ["Please limit your query to 500 characters"]
        }
    
    # Check for potentially problematic queries
    if re.search(r'^[^\w\s]+$', clean_q):
        return {
            "valid": False,
            "error": "Query contains only special characters",
            "suggestions": ["Please use meaningful search terms"]
        }
    
    suggestions = []
    
    # Suggest improvements
    if len(clean_q.split()) == 1:
        suggestions.append("Consider adding more specific terms for better results")
    
    if not re.search(r'[a-zA-Z]', clean_q):
        suggestions.append("Consider including alphabetic characters in your search")
    
    return {
        "valid": True,
        "cleaned_query": clean_q,
        "suggestions": suggestions
    }

def preprocess_query_for_search(query: str, search_type: str = "hybrid") -> Dict[str, Any]:
    """
    Complete query preprocessing pipeline for different search types
    
    Args:
        query: Raw input query
        search_type: Type of search ("semantic", "keyword", "hybrid")
    
    Returns:
        Processed query data
    """
    try:
        # Validate query
        validation = validate_query(query)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "suggestions": validation["suggestions"]
            }
        
        # Extract search terms
        terms = extract_search_terms(query)
        
        # Prepare query for specific search type
        if search_type == "semantic":
            # For semantic search, use cleaned query
            processed_query = terms["cleaned_query"]
        elif search_type == "keyword":
            # For keyword search, might want to use original formatting
            processed_query = terms["keywords"]
        else:  # hybrid
            # For hybrid search, use cleaned query with potential expansions
            processed_query = terms["cleaned_query"]
        
        return {
            "success": True,
            "processed_query": processed_query,
            "search_terms": terms,
            "search_type": search_type,
            "metadata": {
                "original_length": len(query),
                "processed_length": len(str(processed_query)),
                "has_quotes": bool(terms["quoted_phrases"]),
                "has_dates": bool(terms["dates"]),
                "has_entities": bool(terms["entities"]),
                "keyword_count": len(terms["keywords"])
            }
        }
        
    except Exception as e:
        logger.error(f"Query preprocessing failed: {str(e)}")
        return {
            "success": False,
            "error": f"Preprocessing error: {str(e)}",
            "suggestions": ["Please try a simpler query"]
        }
