from elasticsearch import Elasticsearch, helpers
import json

INDEX_NAME = "news_passages_v1"

def create_index(es, dim):
    mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "integer"},
                "passage_id": {"type": "keyword"},
                "title": {"type": "text"},
                "content": {"type": "text"},
                "content_vector": {"type": "dense_vector", "dims": dim}
            }
        }
    }
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
    es.indices.create(index=INDEX_NAME, body=mapping)

def run_indexing(es, input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    create_index(es, dim=len(data[0]["content_vector"]))
    helpers.bulk(es, ({"_index": INDEX_NAME, "_id": d["passage_id"], "_source": d} for d in data))
    return len(data)
