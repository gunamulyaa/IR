import json
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def chunk_by_sentences(text, max_words=180, overlap=40):
    sents = sent_tokenize(text)
    chunks, cur, cur_len = [], [], 0
    for s in sents:
        words = word_tokenize(s)
        if cur_len + len(words) <= max_words:
            cur.append(s)
            cur_len += len(words)
        else:
            if cur:
                chunks.append(" ".join(cur))
            if overlap and chunks:
                prev_words = chunks[-1].split()
                overlap_words = prev_words[-overlap:] if len(prev_words) >= overlap else prev_words
                cur = [" ".join(overlap_words), s]
                cur_len = len(overlap_words) + len(words)
            else:
                cur = [s]
                cur_len = len(words)
    if cur:
        chunks.append(" ".join(cur))
    return [clean_text(c).lower() for c in chunks if c.strip()]

def run_preprocessing(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        docs = json.load(f)

    records = []
    for i, d in enumerate(docs):
        passages = chunk_by_sentences(clean_text(d.get("content", "")))
        for pid, p in enumerate(passages):
            records.append({
                "doc_id": i,
                "passage_id": f"{i}-{pid}",
                "title": d.get("title", ""),
                "content": p
            })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    return len(records)
