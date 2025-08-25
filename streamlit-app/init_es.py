import requests, json, time
from settings import ES_HOST, ES_INDEX, VECTOR_DIMS

def wait_es():
    for _ in range(60):
        try:
            r = requests.get(ES_HOST, timeout=3)
            if r.ok:
                return
        except Exception:
            pass
        time.sleep(2)
    raise RuntimeError("Elasticsearch tidak siap-siap juga.")

def create_index():
    mapping = {
        "settings": {
            "number_of_shards": 1
        },
        "mappings": {
            "properties": {
                "id":      {"type": "keyword"},
                "title":   {"type": "text"},
                "content": {"type": "text"},
                "text":    {"type": "text"},  # dari file embedding (opsional)
                "vector":  {"type": "dense_vector", "dims": VECTOR_DIMS, "index": True, "similarity": "cosine"},
                "url":     {"type": "keyword"},
                "date":    {"type": "date", "format": "strict_date_optional_time||epoch_millis"},
                "tags":    {"type": "keyword"}
            }
        }
    }
    # drop kalau ada
    requests.delete(f"{ES_HOST}/{ES_INDEX}")
    r = requests.put(f"{ES_HOST}/{ES_INDEX}", data=json.dumps(mapping),
                     headers={"Content-Type": "application/json"})
    print(r.status_code, r.text)

if __name__ == "__main__":
    wait_es()
    create_index()
