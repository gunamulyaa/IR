import os

ES_HOST  = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "docs")

MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
VECTOR_DIMS = int(os.getenv("VECTOR_DIMS", "384"))
