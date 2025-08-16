import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    logger.warning(f"Failed to download NLTK data: {str(e)}")

def clean_text(text: str) -> str:
    """Enhanced text cleaning with better preprocessing"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    
    # Remove email addresses
    text = re.sub(r"\S+@\S+", " ", text)
    
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    # Remove special characters but keep Indonesian letters
    text = re.sub(r"[^\w\s\.\,\!\?\;\:\-\(\)]", " ", text)
    
    # Normalize dashes and quotes
    text = re.sub(r"[–—]", "-", text)
    text = re.sub(r"[""''`]", '"', text)
    
    return text

def chunk_by_sentences(text: str, max_words: int = 180, overlap: int = 40) -> List[str]:
    """
    Enhanced sentence-based chunking with better overlap handling
    
    Args:
        text: Input text to chunk
        max_words: Maximum words per chunk
        overlap: Number of words to overlap between chunks
    
    Returns:
        List of text chunks
    """
    try:
        sents = sent_tokenize(text)
        chunks, cur, cur_len = [], [], 0
        
        for s in sents:
            words = word_tokenize(s)
            
            # If current sentence + current chunk exceeds max_words
            if cur_len + len(words) <= max_words:
                cur.append(s)
                cur_len += len(words)
            else:
                # Save current chunk if it has content
                if cur:
                    chunk_text = " ".join(cur)
                    chunks.append(chunk_text)
                
                # Create overlap for next chunk
                if overlap and chunks:
                    prev_words = chunks[-1].split()
                    overlap_words = prev_words[-overlap:] if len(prev_words) >= overlap else prev_words
                    cur = [" ".join(overlap_words), s]
                    cur_len = len(overlap_words) + len(words)
                else:
                    cur = [s]
                    cur_len = len(words)
        
        # Don't forget the last chunk
        if cur:
            chunk_text = " ".join(cur)
            chunks.append(chunk_text)
        
        # Clean and filter chunks
        cleaned_chunks = []
        for chunk in chunks:
            clean_chunk = clean_text(chunk).lower()
            if clean_chunk.strip() and len(clean_chunk.split()) >= 10:  # Minimum 10 words
                cleaned_chunks.append(clean_chunk)
        
        return cleaned_chunks
        
    except Exception as e:
        logger.error(f"Error in chunking: {str(e)}")
        # Fallback: simple word-based chunking
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words - overlap):
            chunk = " ".join(words[i:i + max_words])
            clean_chunk = clean_text(chunk).lower()
            if clean_chunk.strip():
                chunks.append(clean_chunk)
        return chunks

def normalize_date(date_str: str) -> str:
    """
    Normalize various date formats to ISO format
    
    Args:
        date_str: Date string in various formats
    
    Returns:
        Normalized date string in ISO format
    """
    if not date_str:
        return datetime.now().isoformat()
    
    # Common date formats to try
    date_formats = [
        "%Y-%m-%d %H:%M:%S",           # 2025-08-01 15:26:55
        "%Y-%m-%dT%H:%M:%S.%fZ",       # 2024-12-11T10:52:40.000000Z
        "%Y-%m-%d",                     # 2025-08-01
        "%Y/%m/%d %H:%M:%S",           # 2025/08/01 15:26:55
        "%d-%m-%Y %H:%M:%S",           # 01-08-2025 15:26:55
        "%d/%m/%Y %H:%M:%S",           # 01/08/2025 15:26:55
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.isoformat()
        except ValueError:
            continue
    
    # If all formats fail, return current time with warning
    logger.warning(f"Could not parse date: {date_str}, using current time")
    return datetime.now().isoformat()

def validate_document(doc: Dict[str, Any]) -> bool:
    """
    Validate document structure and content
    
    Args:
        doc: Document dictionary
    
    Returns:
        True if document is valid, False otherwise
    """
    # Check required fields
    if not doc.get("title") and not doc.get("content"):
        return False
    
    # Check content length
    content = doc.get("content", "")
    if len(content.strip()) < 50:  # Minimum 50 characters
        return False
    
    # Check for meaningful content (not just special characters)
    word_count = len(re.findall(r'\w+', content))
    if word_count < 10:  # Minimum 10 words
        return False
    
    return True

def run_preprocessing(input_path: str, output_path: str) -> int:
    """
    Enhanced preprocessing with better error handling and validation
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
    
    Returns:
        Number of processed passages
    """
    try:
        logger.info(f"📂 Loading documents from {input_path}")
        
        # Load and validate input file
        with open(input_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        
        if not docs:
            raise ValueError("No documents found in input file")
        
        logger.info(f"📊 Loaded {len(docs)} documents")
        
        records = []
        skipped_docs = 0
        
        for i, doc in enumerate(docs):
            try:
                # Validate document
                if not validate_document(doc):
                    skipped_docs += 1
                    logger.warning(f"Skipped invalid document {i}")
                    continue
                
                # Clean and extract content
                title = clean_text(doc.get("title", ""))
                content = clean_text(doc.get("content", ""))
                
                # Normalize date
                date_str = doc.get("date", "")
                normalized_date = normalize_date(date_str)
                
                # Create chunks
                passages = chunk_by_sentences(content, max_words=180, overlap=40)
                
                if not passages:
                    logger.warning(f"No valid passages created for document {i}")
                    skipped_docs += 1
                    continue
                
                # Create passage records
                for pid, passage in enumerate(passages):
                    record = {
                        "doc_id": i,
                        "passage_id": f"{i}-{pid}",
                        "title": title,
                        "content": passage,
                        "date": normalized_date,
                        "original_doc_index": i,
                        "passage_index": pid,
                        "total_passages": len(passages)
                    }
                    records.append(record)
                
                # Log progress for large datasets
                if (i + 1) % 100 == 0:
                    logger.info(f"📈 Processed {i + 1}/{len(docs)} documents")
                    
            except Exception as e:
                logger.error(f"Error processing document {i}: {str(e)}")
                skipped_docs += 1
                continue
        
        # Save results
        logger.info(f"💾 Saving {len(records)} passages to {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        # Summary statistics
        total_docs = len(docs)
        processed_docs = total_docs - skipped_docs
        
        logger.info(f"✅ Preprocessing completed!")
        logger.info(f"📊 Statistics:")
        logger.info(f"   - Total documents: {total_docs}")
        logger.info(f"   - Processed documents: {processed_docs}")
        logger.info(f"   - Skipped documents: {skipped_docs}")
        logger.info(f"   - Total passages: {len(records)}")
        logger.info(f"   - Average passages per document: {len(records) / max(processed_docs, 1):.1f}")
        
        return len(records)
        
    except FileNotFoundError:
        logger.error(f"❌ Input file not found: {input_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in input file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"❌ Preprocessing failed: {str(e)}")
        raise

def get_preprocessing_stats(output_path: str) -> Dict[str, Any]:
    """
    Get statistics about preprocessed data
    
    Args:
        output_path: Path to preprocessed JSON file
    
    Returns:
        Dictionary with statistics
    """
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data:
            return {"error": "No data found"}
        
        # Calculate statistics
        total_passages = len(data)
        unique_docs = len(set(record["doc_id"] for record in data))
        avg_passage_length = sum(len(record["content"].split()) for record in data) / total_passages
        
        # Date range
        dates = [record.get("date") for record in data if record.get("date")]
        date_range = {"earliest": min(dates), "latest": max(dates)} if dates else {"error": "No dates found"}
        
        return {
            "total_passages": total_passages,
            "unique_documents": unique_docs,
            "avg_passages_per_doc": round(total_passages / unique_docs, 1),
            "avg_passage_length_words": round(avg_passage_length, 1),
            "date_range": date_range
        }
        
    except Exception as e:
        logger.error(f"Failed to get preprocessing stats: {str(e)}")
        return {"error": str(e)}
