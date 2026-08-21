"""
SBERT (Sentence-BERT) - embedding ngữ nghĩa dense cho tiêu đề câu hỏi.

Theo lưu ý Phần 6 kế hoạch: KHÔNG tự train, dùng thẳng model pretrained
(`paraphrase-multilingual-MiniLM-L12-v2`, cấu hình ở core/config.py).

Chiến lược <1s: model load 1 lần lúc khởi động (giữ RAM suốt vòng đời service), toàn bộ
embedding của câu hỏi cache thành 1 ma trận numpy để search bằng brute-force cosine
(nhân ma trận) - đủ nhanh với vài nghìn bản ghi. Khi dataset > 5.000 câu hỏi, thay
bước brute-force này bằng MongoDB Atlas `$vectorSearch` hoặc Qdrant HNSW (xem README).
"""
import time
from datetime import datetime, timezone

import numpy as np

from app.core.config import settings
from app.core.database import questions_col, question_vectors_sbert_col

_model = None  # lazy singleton - load 1 lần


class _Cache:
    def __init__(self):
        self.question_ids: list[str] = []
        self.matrix: np.ndarray | None = None  # shape (n_docs, dim), đã L2-normalize từng hàng
        self.dimension: int = 0
        self.loaded = False


_cache = _Cache()


def get_model():
    """Load model SBERT 1 lần (lazy singleton). Trả None nếu môi trường chưa cài được
    sentence-transformers hoặc không tải được model (không có mạng) - endpoint sẽ báo lỗi rõ ràng
    thay vì crash cả app lúc khởi động."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(settings.sbert_model_name)
        except Exception as e:  # pragma: no cover - phụ thuộc môi trường triển khai
            print(f"[SBERT] Không load được model '{settings.sbert_model_name}': {e}")
            _model = False  # đánh dấu "đã thử và lỗi" để không thử lại mỗi request
    return _model or None


def _normalize_rows(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


async def load_cache_from_db():
    """Load toàn bộ embedding đã lưu từ MongoDB vào RAM - gọi lúc app khởi động."""
    docs = [d async for d in question_vectors_sbert_col.find({})]
    if not docs:
        _cache.loaded = True
        return
    _cache.question_ids = [str(d["questionId"]) for d in docs]
    mat = np.array([d["embedding"] for d in docs], dtype=np.float32)
    _cache.matrix = _normalize_rows(mat)
    _cache.dimension = mat.shape[1]
    _cache.loaded = True


async def reindex_all() -> dict:
    """Encode lại TOÀN BỘ tiêu đề câu hỏi bằng SBERT, lưu MongoDB + cache RAM."""
    model = get_model()
    if model is None:
        return {"indexed": 0, "error": "SBERT model chưa sẵn sàng (xem log server)"}

    t0 = time.perf_counter()
    questions = [q async for q in questions_col.find({}, {"title": 1})]
    if not questions:
        return {"indexed": 0, "elapsedMs": 0}

    titles = [q["title"] for q in questions]
    embeddings = model.encode(titles, show_progress_bar=False, convert_to_numpy=True)
    dimension = int(embeddings.shape[1])

    writes = []
    now = datetime.now(timezone.utc)
    for q, emb in zip(questions, embeddings):
        writes.append(
            {
                "questionId": q["_id"],
                "embedding": emb.astype(float).tolist(),
                "modelName": settings.sbert_model_name,
                "dimension": dimension,
                "updatedAt": now,
            }
        )

    await question_vectors_sbert_col.delete_many({})
    if writes:
        # upsert riêng từng doc (thay vì insert_many) để tránh trùng nếu gọi song song với TF-IDF reindex
        for w in writes:
            await question_vectors_sbert_col.update_one({"questionId": w["questionId"]}, {"$set": w}, upsert=True)
    await questions_col.update_many({}, {"$set": {"isIndexed": True}})

    _cache.question_ids = [str(q["_id"]) for q in questions]
    _cache.matrix = _normalize_rows(np.array(embeddings, dtype=np.float32))
    _cache.dimension = dimension
    _cache.loaded = True

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {"indexed": len(questions), "dimension": dimension, "elapsedMs": round(elapsed_ms, 2)}


async def index_single_question(question_id, title: str):
    """Encode + lưu embedding cho 1 câu hỏi mới/sửa - không cần retrain gì (khác TF-IDF)."""
    model = get_model()
    if model is None:
        return
    embedding = model.encode([title], show_progress_bar=False, convert_to_numpy=True)[0]
    doc = {
        "questionId": question_id,
        "embedding": embedding.astype(float).tolist(),
        "modelName": settings.sbert_model_name,
        "dimension": int(embedding.shape[0]),
        "updatedAt": datetime.now(timezone.utc),
    }
    await question_vectors_sbert_col.update_one({"questionId": question_id}, {"$set": doc}, upsert=True)
    await questions_col.update_one({"_id": question_id}, {"$set": {"isIndexed": True}})

    qid_str = str(question_id)
    row = _normalize_rows(embedding.reshape(1, -1))
    if qid_str in _cache.question_ids:
        idx = _cache.question_ids.index(qid_str)
        _cache.matrix[idx] = row[0]
    elif _cache.matrix is not None and _cache.matrix.shape[1] == row.shape[1]:
        _cache.matrix = np.vstack([_cache.matrix, row])
        _cache.question_ids.append(qid_str)
    else:
        _cache.matrix = row
        _cache.question_ids = [qid_str]


def get_stats() -> dict:
    return {"indexedCount": len(_cache.question_ids), "dimension": _cache.dimension, "modelLoaded": _model not in (None, False)}


async def remove_question(question_id):
    """Dọn embedding của 1 câu hỏi đã bị xóa - khỏi DB và khỏi cache RAM."""
    await question_vectors_sbert_col.delete_one({"questionId": question_id})
    qid_str = str(question_id)
    if qid_str in _cache.question_ids:
        idx = _cache.question_ids.index(qid_str)
        _cache.question_ids.pop(idx)
        if _cache.matrix is not None:
            _cache.matrix = np.delete(_cache.matrix, idx, axis=0)


def search(query: str, top_k: int = 10) -> list[tuple[str, float]]:
    """Trả về [(questionId, cosineScore), ...] top-K, dùng brute-force cosine (ma trận đã normalize)."""
    model = get_model()
    if model is None or _cache.matrix is None or not _cache.question_ids:
        return []
    q_emb = model.encode([query], show_progress_bar=False, convert_to_numpy=True)[0]
    q_emb = q_emb / (np.linalg.norm(q_emb) or 1.0)
    scores = _cache.matrix @ q_emb  # (n_docs,) - vì cả 2 phía đã L2-normalize -> tích vô hướng = cosine
    top_idx = np.argsort(-scores)[:top_k]
    return [(_cache.question_ids[i], float(scores[i])) for i in top_idx if scores[i] > 0]
