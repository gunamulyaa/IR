from sentence_transformers import SentenceTransformer
from .query_preprocessing import clean_query

INDEX_NAME = "news_passages_v1"
MODEL_NAME = "all-MiniLM-L6-v2"

def run_retrieval(es, query, k=5):
    model = SentenceTransformer(MODEL_NAME)
    q_vec = model.encode(clean_query(query), normalize_embeddings=True).tolist()
    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                "params": {"query_vector": q_vec}
            }
        }
    }
    resp = es.search(index=INDEX_NAME, body={"size": k, "query": script_query})
    return [
        {"score": h["_score"], "title": h["_source"]["title"], "content": h["_source"]["content"]}
        for h in resp["hits"]["hits"]
    ]
