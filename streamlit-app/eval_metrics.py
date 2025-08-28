# eval_metrics.py
from typing import Dict, List, Iterable, Set, Tuple, Optional
import math
import numpy as np

# ---------- METRIK DASAR (punyamu) ----------
def precision_at_k(relevant: Iterable[str], retrieved: List[str], k: int) -> float:
    retrieved_k = retrieved[:k]
    relevant_set = set(relevant)
    tp = len(relevant_set.intersection(retrieved_k))
    return (tp / k) if k > 0 else 0.0

def recall_at_k(relevant: Iterable[str], retrieved: List[str], k: int) -> float:
    relevant_set = set(relevant)
    if len(relevant_set) == 0:
        return 0.0
    retrieved_k = retrieved[:k]
    tp = len(set(retrieved_k).intersection(relevant_set))
    return tp / len(relevant_set)

def mean_reciprocal_rank(qrels: Dict[str, List[str]], results: Dict[str, List[str]]) -> float:
    mrrs: List[float] = []
    for qid, rel_docs in qrels.items():
        rel_set = set(rel_docs)
        ranked = results.get(qid, [])
        rr = 0.0
        for rank, d in enumerate(ranked, start=1):
            if d in rel_set:
                rr = 1.0 / rank
                break
        mrrs.append(rr)
    return float(np.mean(mrrs)) if mrrs else 0.0

# ---------- TAMBAHKAN: AP & MAP (biner) ----------
def average_precision(relevant: Iterable[str], retrieved: List[str]) -> float:
    rel_set = set(relevant)
    if not rel_set:
        return 0.0
    score, hits = 0.0, 0
    for i, d in enumerate(retrieved, start=1):
        if d in rel_set:
            hits += 1
            score += hits / i
    return score / len(rel_set)

def mean_average_precision(qrels_bin: Dict[str, Iterable[str]], results: Dict[str, List[str]]) -> float:
    aps: List[float] = []
    for qid, rel_iter in qrels_bin.items():
        aps.append(average_precision(rel_iter, results.get(qid, [])))
    return float(np.mean(aps)) if aps else 0.0

# ---------- TAMBAHKAN: DCG / nDCG (graded) ----------
def dcg_at_k(gains: List[float], k: int, use_log: bool = True) -> float:
    """gains = daftar gain sesuai urutan hasil retrieve, mis. [3,0,2,...]"""
    gains = gains[:k]
    if not gains:
        return 0.0
    if not use_log:
        return float(sum(gains))
    return float(sum(g / math.log2(i + 2) for i, g in enumerate(gains)))

def ndcg_at_k(relevances_ranked: List[int], k: int, use_exp_gain: bool = False) -> float:
    """
    relevances_ranked: daftar relevansi sesuai ranking (0..3/4/5)
    use_exp_gain=True => gain = 2^rel - 1 (lebih peka pada relevansi tinggi)
    """
    if use_exp_gain:
        gains = [(2**r - 1) for r in relevances_ranked]
        ideal = sorted(gains, reverse=True)
    else:
        gains = list(relevances_ranked)
        ideal = sorted(relevances_ranked, reverse=True)

    dcg = dcg_at_k(gains, k)
    idcg = dcg_at_k(ideal, k)
    return (dcg / idcg) if idcg > 0 else 0.0

def mean_ndcg_at_k(qrels_graded: Dict[str, Dict[str, int]],
                   results: Dict[str, List[str]],
                   k: int,
                   use_exp_gain: bool = False) -> float:
    ndcgs: List[float] = []
    for qid, rel_map in qrels_graded.items():
        ranked = results.get(qid, [])
        rels_ranked = [rel_map.get(doc_id, 0) for doc_id in ranked]
        ndcgs.append(ndcg_at_k(rels_ranked, k, use_exp_gain=use_exp_gain))
    return float(np.mean(ndcgs)) if ndcgs else 0.0

# ---------- TAMBAHKAN: metrik pendamping ----------
def hit_rate_at_k(relevant: Iterable[str], retrieved: List[str], k: int) -> float:
    """1 jika ada minimal satu relevan di top-k, else 0. Dirata-ratakan lintas kueri."""
    rel_set = set(relevant)
    return 1.0 if any(d in rel_set for d in retrieved[:k]) else 0.0

def r_precision(relevant: Iterable[str], retrieved: List[str]) -> float:
    """Precision pada R, di mana R = jumlah dokumen relevan untuk kueri tsb."""
    rel_set = set(relevant)
    R = len(rel_set)
    if R == 0:
        return 0.0
    topR = retrieved[:R]
    tp = len(set(topR).intersection(rel_set))
    return tp / R

def f1_at_k(relevant: Iterable[str], retrieved: List[str], k: int) -> float:
    p = precision_at_k(relevant, retrieved, k)
    r = recall_at_k(relevant, retrieved, k)
    return (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

# ---------- UTIL: konversi graded -> biner ----------
def binarize_qrels(qrels_graded: Dict[str, Dict[str, int]], threshold: int = 1) -> Dict[str, Set[str]]:
    """
    threshold=1: rel>=1 dianggap relevan
    return: {qid: set(doc_id relevan)}
    """
    out: Dict[str, Set[str]] = {}
    for qid, relmap in qrels_graded.items():
        out[qid] = {d for d, g in relmap.items() if g >= threshold}
    return out

# ---------- CONTOH AGREGASI ALL-IN ----------
def evaluate_runs(qrels_graded: Dict[str, Dict[str, int]],
                  runs: Dict[str, List[str]],
                  k: int = 10,
                  use_exp_gain: bool = False) -> Dict[str, float]:
    """
    qrels_graded: {qid: {doc_id: grade_int}}
    runs: {qid: [doc_ids dalam urutan ranking]}
    """
    qrels_bin = binarize_qrels(qrels_graded, threshold=1)

    # per-kueri untuk rata-rata macro
    p_list, r_list, f1_list, hr_list, rp_list, nd_list, ap_list, rr_list = [], [], [], [], [], [], [], []

    for qid, relmap in qrels_graded.items():
        ranked = runs.get(qid, [])
        # graded
        rels_ranked = [relmap.get(doc_id, 0) for doc_id in ranked]
        nd_list.append(ndcg_at_k(rels_ranked, k, use_exp_gain=use_exp_gain))
        # biner
        relset = qrels_bin.get(qid, set())
        p_list.append(precision_at_k(relset, ranked, k))
        r_list.append(recall_at_k(relset, ranked, k))
        f1_list.append(f1_at_k(relset, ranked, k))
        hr_list.append(hit_rate_at_k(relset, ranked, k))
        rp_list.append(r_precision(relset, ranked))
        ap_list.append(average_precision(relset, ranked))
        # RR per kueri
        rr = 0.0
        for rank, d in enumerate(ranked, start=1):
            if d in relset:
                rr = 1.0 / rank
                break
        rr_list.append(rr)

    return {
        f"P@{k}": float(np.mean(p_list)) if p_list else 0.0,
        f"R@{k}": float(np.mean(r_list)) if r_list else 0.0,
        f"F1@{k}": float(np.mean(f1_list)) if f1_list else 0.0,
        "HitRate@k": float(np.mean(hr_list)) if hr_list else 0.0,
        "R-Precision": float(np.mean(rp_list)) if rp_list else 0.0,
        f"nDCG@{k}": float(np.mean(nd_list)) if nd_list else 0.0,
        "MAP": float(np.mean(ap_list)) if ap_list else 0.0,
        "MRR": float(np.mean(rr_list)) if rr_list else 0.0,
    }
