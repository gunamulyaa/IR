import re

def clean_query(q):
    q = re.sub(r"https?://\S+", "", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q.lower()
