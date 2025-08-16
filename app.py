import streamlit as st
import os
import time
from datetime import datetime, timedelta
from steps.elasticsearch_config import ElasticsearchManager
from steps.preprocessing import run_preprocessing, get_preprocessing_stats
from steps.embedding import run_embedding
from steps.indexing import run_indexing, get_index_info
from steps.retrieval import EnhancedRetrieval
from steps.query_preprocessing import preprocess_query_for_search

# Configure Streamlit page
st.set_page_config(
    page_title="IR System - Pencarian Berita",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File paths
DATA_RAW = "Data/combined_articles.json"
DATA_PREPROCESSED = "Data/preprocessed.json"
DATA_EMBEDDED = "Data/embedded.json"

# Elasticsearch configuration
ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_USER = os.getenv("ES_USER", None)
ES_PASS = os.getenv("ES_PASS", None)

@st.cache_resource
def get_elasticsearch_manager():
    """Get cached Elasticsearch manager"""
    return ElasticsearchManager(host=ES_HOST, username=ES_USER, password=ES_PASS)

@st.cache_resource
def get_retrieval_system():
    """Get cached retrieval system"""
    es_manager = get_elasticsearch_manager()
    return EnhancedRetrieval(es_manager)

def is_valid_json(path):
    """Check if file exists and is not empty"""
    return os.path.exists(path) and os.path.getsize(path) > 0

def run_pipeline_with_progress():
    """Run the complete pipeline with progress tracking"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Preprocessing
        if not is_valid_json(DATA_PREPROCESSED):
            status_text.text("🔄 Step 1/3: Preprocessing documents...")
            progress_bar.progress(10)
            
            passages_count = run_preprocessing(DATA_RAW, DATA_PREPROCESSED)
            st.success(f"✅ Preprocessing completed: {passages_count} passages created")
            progress_bar.progress(33)
        else:
            st.info("ℹ️ Preprocessing already completed")
            progress_bar.progress(33)

        # Step 2: Embedding
        if not is_valid_json(DATA_EMBEDDED):
            status_text.text("🔄 Step 2/3: Creating embeddings...")
            progress_bar.progress(40)
            
            embedded_count = run_embedding(DATA_PREPROCESSED, DATA_EMBEDDED)
            st.success(f"✅ Embedding completed: {embedded_count} embeddings created")
            progress_bar.progress(66)
        else:
            st.info("ℹ️ Embeddings already created")
            progress_bar.progress(66)

        # Step 3: Indexing
        status_text.text("🔄 Step 3/3: Indexing to Elasticsearch...")
        progress_bar.progress(70)
        
        es_manager = get_elasticsearch_manager()
        indexed_count = run_indexing(es_manager, DATA_EMBEDDED)
        st.success(f"✅ Indexing completed: {indexed_count} documents indexed")
        progress_bar.progress(100)
        
        status_text.text("✅ Pipeline completed successfully!")
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        return True
        
    except Exception as e:
        st.error(f"❌ Pipeline failed: {str(e)}")
        progress_bar.empty()
        status_text.empty()
        return False

# Initialize pipeline
@st.cache_data
def init_pipeline():
    """Initialize the pipeline once"""
    return run_pipeline_with_progress()

# Sidebar - System Status
with st.sidebar:
    st.header("🔧 System Status")
    
    # Elasticsearch health check
    try:
        es_manager = get_elasticsearch_manager()
        health = es_manager.health_check()
        if health.get("status") == "green":
            st.success("🟢 Elasticsearch: Healthy")
        elif health.get("status") == "yellow":
            st.warning("🟡 Elasticsearch: Warning")
        else:
            st.error("🔴 Elasticsearch: Error")
    except Exception as e:
        st.error(f"🔴 Elasticsearch: Connection Failed")
    
    # File status
    st.subheader("📁 Data Files")
    files_status = {
        "Raw Data": DATA_RAW,
        "Preprocessed": DATA_PREPROCESSED,
        "Embedded": DATA_EMBEDDED
    }
    
    for name, path in files_status.items():
        if is_valid_json(path):
            st.success(f"✅ {name}")
        else:
            st.error(f"❌ {name}")
    
    # System metrics
    st.subheader("📊 System Metrics")
    if is_valid_json(DATA_PREPROCESSED):
        try:
            stats = get_preprocessing_stats(DATA_PREPROCESSED)
            if "error" not in stats:
                st.metric("Total Passages", stats["total_passages"])
                st.metric("Documents", stats["unique_documents"])
                st.metric("Avg Words/Passage", stats["avg_passage_length_words"])
        except Exception:
            st.warning("Could not load stats")
    
    # Index information
    try:
        es_manager = get_elasticsearch_manager()
        index_info = get_index_info(es_manager)
        if "error" not in index_info:
            st.subheader("🗂️ Index Info")
            st.metric("Indexed Documents", index_info["stats"]["document_count"])
            st.metric("Index Size (MB)", index_info["stats"]["size_mb"])
    except Exception:
        pass

# Main Application
st.title("🔍 Information Retrieval System")
st.markdown("**Advanced News Search with Semantic & Keyword Search**")

# Initialize pipeline
if st.button("🔄 Initialize/Refresh Pipeline"):
    with st.spinner("Initializing pipeline..."):
        init_pipeline()

# Initialize once on app start
if "pipeline_initialized" not in st.session_state:
    with st.spinner("Loading system..."):
        init_pipeline()
    st.session_state.pipeline_initialized = True

# Search Interface
st.header("🔍 Search Interface")

# Search configuration
col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Enter your search query:",
        placeholder="e.g., teknologi artificial intelligence, dampak perubahan iklim",
        help="Use specific terms for better results. You can search in Indonesian or English."
    )

with col2:
    search_type = st.selectbox(
        "Search Mode:",
        ["hybrid", "semantic", "keyword"],
        help="Hybrid combines semantic and keyword search for best results"
    )

# Advanced options
with st.expander("🔧 Advanced Search Options"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_k = st.slider("Number of results", 1, 20, 5)
        min_score = st.slider("Minimum relevance score", 0.0, 2.0, 0.5, 0.1)
    
    with col2:
        if search_type == "hybrid":
            semantic_weight = st.slider("Semantic weight", 0.0, 1.0, 0.7, 0.1)
        else:
            semantic_weight = 0.7
    
    with col3:
        # Date filter
        use_date_filter = st.checkbox("Filter by date range")
        if use_date_filter:
            start_date = st.date_input("From date", datetime.now() - timedelta(days=365))
            end_date = st.date_input("To date", datetime.now())

# Search execution
if st.button("🔍 Search", type="primary") and query.strip():
    # Preprocess query
    query_data = preprocess_query_for_search(query, search_type)
    
    if not query_data["success"]:
        st.error(f"❌ {query_data['error']}")
        if query_data.get("suggestions"):
            st.info("💡 Suggestions: " + ", ".join(query_data["suggestions"]))
    else:
        with st.spinner("Searching..."):
            try:
                # Get retrieval system
                retrieval = get_retrieval_system()
                
                # Prepare search parameters
                search_params = {
                    "query": query,
                    "k": top_k,
                    "min_score": min_score
                }
                
                if search_type == "hybrid":
                    search_params["semantic_weight"] = semantic_weight
                    
                    # Add date filter if enabled
                    if use_date_filter:
                        search_params["date_filter"] = {
                            "from": start_date.strftime("%Y-%m-%d"),
                            "to": end_date.strftime("%Y-%m-%d")
                        }
                    
                    results = retrieval.hybrid_search(**search_params)
                    
                elif search_type == "semantic":
                    results = retrieval.semantic_search_only(query, top_k)
                    
                else:  # keyword
                    results = retrieval.keyword_search_only(query, top_k)
                
                # Display results
                if results:
                    st.success(f"✅ Found {len(results)} results")
                    
                    # Query information
                    with st.expander("ℹ️ Query Information"):
                        st.json(query_data["search_terms"])
                    
                    # Results
                    for i, result in enumerate(results, 1):
                        with st.container():
                            st.markdown(f"### {i}. {result['title']}")
                            
                            # Result metadata
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Relevance Score", f"{result['score']:.3f}")
                            with col2:
                                st.metric("Word Count", result.get('word_count', 'N/A'))
                            with col3:
                                date_str = result.get('date', '')
                                if date_str:
                                    try:
                                        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                        st.metric("Date", date_obj.strftime("%Y-%m-%d"))
                                    except:
                                        st.metric("Date", "N/A")
                                else:
                                    st.metric("Date", "N/A")
                            with col4:
                                st.metric("Passage ID", result.get('passage_id', 'N/A'))
                            
                            # Content
                            st.markdown("**Content:**")
                            st.write(result['content'])
                            
                            # Similarity search button
                            if st.button(f"🔗 Find Similar", key=f"similar_{i}"):
                                try:
                                    similar_results = retrieval.get_similar_articles(result['id'], k=3)
                                    if similar_results:
                                        st.write("**Similar Articles:**")
                                        for sim_result in similar_results:
                                            st.write(f"- {sim_result['title']} (Score: {sim_result['score']:.3f})")
                                    else:
                                        st.info("No similar articles found")
                                except Exception as e:
                                    st.warning(f"Could not find similar articles: {str(e)}")
                            
                            st.markdown("---")
                else:
                    st.warning("🔍 No results found. Try:")
                    st.info("• Using different keywords\n• Reducing minimum score\n• Using hybrid search mode\n• Checking spelling")
                    
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")
                st.info("💡 Try refreshing the page or checking system status")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Information Retrieval System - Enhanced with Elasticsearch & Semantic Search</p>
    <p>Team: Muhammad Ashabul Kahfi, Furqan S.T, Kadek Gunamulya, Abdul Razak Aliudin</p>
</div>
""", unsafe_allow_html=True)
