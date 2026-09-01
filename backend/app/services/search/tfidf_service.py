"""
TF-IDF (Vector Space Model cổ điển) cho tìm kiếm câu hỏi theo tiêu đề.

Chiến lược <1s (Phần 4 kế hoạch): toàn bộ vocabulary + vector của mọi câu hỏi được cache
trong RAM (biến module-level `_cache`), không query lại MongoDB ở mỗi lần search - chỉ
đọc DB lúc khởi động service hoặc sau khi reindex.
"""
import time
from datetime import datetime, timezone
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.database import questions_col, question_vectors_tfidf_col, tfidf_vocabulary_col
from app.services.search.preprocess import preprocess

VOCAB_DOC_ID = "current"


class _Cache:
    """Cache RAM: vocab (term->index), idf (index->weight), và vector từng câu hỏi."""

    def __init__(self):
        self.vocab: dict[str, int] = {}
        self.idf: dict[int, float] = {}
        self.dimension: int = 0
        self.version: int = 0
        # question_id (str) -> (vectorSparse: dict[int, float], norm: float)
        self.doc_vectors: dict[str, tuple[dict, float]] = {}
        self.loaded = False


_cache = _Cache()


def _encode_tokens(tokens: list[str]) -> tuple[dict[int, float], float]:
    """Encode 1 danh sách token thành vector TF-IDF thưa, dùng vocab/idf hiện hành trong cache."""
    tf = Counter(t for t in tokens if t in _cache.vocab)
    vector: dict[int, float] = {}
    for term, count in tf.items():
        idx = _cache.vocab[term]
        vector[idx] = count * _cache.idf.get(idx, 0.0)
    norm = float(np.sqrt(sum(w * w for w in vector.values())))
    return vector, norm


def encode_title(title: str) -> tuple[dict[int, float], float]:
    return _encode_tokens(preprocess(title))


import difflib


def encode_query(query: str) -> tuple[dict[int, float], float]:
    tokens = preprocess(query)
    resolved_tokens = []
    vocab_keys = list(_cache.vocab.keys())

    for t in tokens:
        if t in _cache.vocab:
            resolved_tokens.append(t)
        else:
            # Fuzzy match: Nếu gõ sai từ (vd: databade -> database), tự động sửa chính tả từ gần nhất
            matches = difflib.get_close_matches(t, vocab_keys, n=1, cutoff=0.7)
            if matches:
                resolved_tokens.append(matches[0])

    return _encode_tokens(resolved_tokens)


def cosine(vec_a: dict[int, float], norm_a: float, vec_b: dict[int, float], norm_b: float) -> float:
    if norm_a == 0 or norm_b == 0:
        return 0.0
    # Dot product qua giao 2 dict thưa - nhanh vì tiêu đề rất ngắn (thường < 15 token khác 0)
    small, big = (vec_a, vec_b) if len(vec_a) < len(vec_b) else (vec_b, vec_a)
    dot = sum(w * big[idx] for idx, w in small.items() if idx in big)
    return dot / (norm_a * norm_b)


async def load_cache_from_db():
    """Load vocab + toàn bộ vector đã lưu từ MongoDB vào RAM - gọi lúc app khởi động."""
    vocab_doc = await tfidf_vocabulary_col.find_one({"_id": VOCAB_DOC_ID})
    if not vocab_doc:
        _cache.loaded = True  # chưa có vocab -> chưa từng reindex, /api/search/tfidf sẽ trả rỗng
        return

    _cache.vocab = vocab_doc["vocab"]
    _cache.idf = {int(k): v for k, v in vocab_doc["idf"].items()}
    _cache.dimension = vocab_doc["dimension"]
    _cache.version = vocab_doc["version"]

    _cache.doc_vectors = {}
    async for v in question_vectors_tfidf_col.find({"vocabVersion": _cache.version}):
        vec = {int(k): val for k, val in v["vectorSparse"].items()}
        _cache.doc_vectors[str(v["questionId"])] = (vec, v["norm"])
    _cache.loaded = True


async def reindex_all() -> dict:
    """
    Xây lại TOÀN BỘ vocabulary + vector từ đầu (dùng khi mới seed data, hoặc dataset đã
    tăng đáng kể - Phần 2.8.2 kế hoạch). Trả về thống kê thời gian để ghi log benchmark.
    Index cả Tiêu đề (nhân đôi trọng số) lẫn Nội dung chi tiết (Body) để tìm kiếm linh hoạt.
    """
    t0 = time.perf_counter()

    questions = [q async for q in questions_col.find({}, {"title": 1, "body": 1})]
    if not questions:
        return {"indexed": 0, "elapsedMs": 0}

    preprocessed = [
        " ".join(preprocess(f"{q.get('title', '')} {q.get('title', '')} {q.get('body', '')}"))
        for q in questions
    ]

    # norm=None: giữ trọng số TF-IDF thô, TỰ tính norm riêng để cosine = dot/(norm_a*norm_b)
    # đúng như công thức trong kế hoạch (Phần 3), thay vì để sklearn tự L2-normalize.
    # max_features=30000 để từ điển tối ưu, kích thước BSON document ~9.5MB, nằm an toàn dưới ngưỡng 16MB của MongoDB.
    vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=lambda x: x,
        token_pattern=None,
        norm=None,
        max_features=30000,
    )
    matrix = vectorizer.fit_transform(preprocessed)  # scipy sparse csr

    new_version = _cache.version + 1 if _cache.loaded and _cache.vocab else 1
    vocab = {term: int(idx) for term, idx in vectorizer.vocabulary_.items()}
    idf = {str(i): float(w) for i, w in enumerate(vectorizer.idf_)}
    dimension = len(vocab)

    await tfidf_vocabulary_col.update_one(
        {"_id": VOCAB_DOC_ID},
        {
            "$set": {
                "version": new_version,
                "vocab": vocab,
                "idf": idf,
                "dimension": dimension,
                "trainedAt": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )

    doc_vector_writes = []
    new_doc_vectors: dict[str, tuple[dict, float]] = {}
    for i, q in enumerate(questions):
        row = matrix.getrow(i)
        vector_sparse = {str(idx): float(val) for idx, val in zip(row.indices, row.data)}
        norm = float(np.sqrt(np.sum(row.data**2))) if row.data.size else 0.0
        doc_vector_writes.append(
            {
                "questionId": q["_id"],
                "vectorSparse": vector_sparse,
                "norm": norm,
                "vocabVersion": new_version,
                "updatedAt": datetime.now(timezone.utc),
            }
        )
        new_doc_vectors[str(q["_id"])] = ({int(k): v for k, v in vector_sparse.items()}, norm)

    # Xóa vector cũ (version cũ) rồi ghi vector mới theo từng batch 50,000 bản ghi
    await question_vectors_tfidf_col.delete_many({})
    batch_size = 50000
    for b in range(0, len(doc_vector_writes), batch_size):
        await question_vectors_tfidf_col.insert_many(doc_vector_writes[b : b + batch_size])

    await questions_col.update_many({}, {"$set": {"isIndexed": True}})

    _cache.vocab = vocab
    _cache.idf = {int(k): v for k, v in idf.items()}
    _cache.dimension = dimension
    _cache.version = new_version
    _cache.doc_vectors = new_doc_vectors
    _cache.loaded = True

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {"indexed": len(questions), "dimension": dimension, "version": new_version, "elapsedMs": round(elapsed_ms, 2)}


async def index_single_question(question_id, title: str, body: str = ""):
    """
    Re-index 1 câu hỏi bằng vocab HIỆN HÀNH (không retrain) - dùng khi tạo/sửa câu hỏi.
    Nếu chưa từng reindex_all() (chưa có vocab), bỏ qua - admin cần trigger reindex trước.
    """
    if not _cache.loaded or not _cache.vocab:
        return
    full_text = f"{title} {title} {body}"
    vec, norm = _encode_tokens(preprocess(full_text))
    doc = {
        "questionId": question_id,
        "vectorSparse": {str(k): v for k, v in vec.items()},
        "norm": norm,
        "vocabVersion": _cache.version,
        "updatedAt": datetime.now(timezone.utc),
    }
    await question_vectors_tfidf_col.update_one({"questionId": question_id}, {"$set": doc}, upsert=True)
    await questions_col.update_one({"_id": question_id}, {"$set": {"isIndexed": True}})
    _cache.doc_vectors[str(question_id)] = (vec, norm)


def get_stats() -> dict:
    return {"indexedCount": len(_cache.doc_vectors), "version": _cache.version, "dimension": _cache.dimension}


async def remove_question(question_id):
    """Dọn vector của 1 câu hỏi đã bị xóa - khỏi DB và khỏi cache RAM."""
    await question_vectors_tfidf_col.delete_one({"questionId": question_id})
    _cache.doc_vectors.pop(str(question_id), None)


def search(query: str, min_score: float = 0.0) -> list[tuple[str, float]]:
    """
    Trả về [(questionId, score), ...] sắp xếp giảm dần theo cosine similarity.
    Không giới hạn top_k — trả về TẤT CẢ kết quả có score > min_score.
    Phân trang xảy ra ở tầng API (router), giống cách Stack Overflow hoạt động thật.
    """
    if not _cache.vocab:
        return []
    q_vec, q_norm = encode_query(query)
    if q_norm == 0:
        return []
    scored = [
        (qid, cosine(q_vec, q_norm, vec, norm))
        for qid, (vec, norm) in _cache.doc_vectors.items()
    ]
    scored = [s for s in scored if s[1] > min_score]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
