"""
TF-IDF (Vector Space Model cổ điển) cho tìm kiếm câu hỏi theo tiêu đề.

Chiến lược <1s (Phần 4 kế hoạch): toàn bộ vocabulary + vector của mọi câu hỏi được cache
trong RAM (biến module-level `_cache`), không query lại MongoDB ở mỗi lần search - chỉ
đọc DB lúc khởi động service hoặc sau khi reindex.

Optimisations:
  1. vocab_keys_sorted — list vocab đã sort sẵn, dùng cho binary-search fuzzy thay vì
     difflib O(V) brute-force mỗi token.
  2. inverted_index — map term_idx -> list[questionId], cho phép search() chỉ duyệt
     những câu hỏi thực sự chứa ít nhất 1 term của query thay vì toàn bộ N_docs.
"""
import bisect
import time

from scipy import sparse as scipy_sparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.database import questions_col, question_vectors_tfidf_col, tfidf_vocabulary_col
from app.services.search.preprocess import preprocess
from app.services.search.query_parser import ParsedQuery, parse_query

VOCAB_DOC_ID = "current"


@dataclass
class _DocMeta:
    """Metadata nhẹ của 1 câu hỏi, giữ trong RAM để áp filter kiểu SO ngay trên bộ đệm
    (không cần query MongoDB mỗi lần tìm kiếm)."""

    title: str
    tags: frozenset[str]
    vote_score: int
    answer_count: int
    has_accepted: bool
    created_ts: float  # epoch seconds
    author_name: str  # lowercase tên tác giả (displayName/username)
    author_id: str = ""  # authorId (str) - dùng cho filter user:me


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
        # Sorted list of vocab keys — built once after load/reindex, dùng cho binary-search fuzzy
        self.vocab_keys_sorted: list[str] = []
        # Inverted index: term_idx (int) -> list of questionId (str)
        # Cho phép search() chỉ duyệt candidate docs thay vì toàn bộ N_docs.
        self.inverted_index: dict[int, list[str]] = {}
        # Metadata nhẹ per doc để áp filter kiểu SO trên RAM (không cần DB call mỗi search).
        self.doc_meta: dict[str, _DocMeta] = {}
        self.users: dict[str, str] = {}  # userId(str) -> authorName (lowercase)
        # ---- Fast-path numpy/scipy cho dataset quy mô lớn (hàng trăm nghìn - triệu docs) ----
        self.doc_ids: list[str] = []          # thứ tự cột của ma trận
        self.doc_norms: np.ndarray | None = None
        self.doc_matrix = None                # scipy sparse CSR (dim x N): hàng = term
        self.created_arr: np.ndarray | None = None
        self.votes_arr: np.ndarray | None = None
        self.meta_exists: np.ndarray | None = None
        self._matrix_dirty = False
        self._meta_arrays_dirty = False

    def rebuild_secondary_indexes(self):
        """Gọi sau mỗi lần vocab hoặc doc_vectors thay đổi hoàn toàn."""
        self.vocab_keys_sorted = sorted(self.vocab.keys())
        self._rebuild_inverted_index()
        # Build lại ma trận CSC + mảng phụ trợ cho fast-path numpy (chạy 1 lần)
        self._ensure_numpy_index(force=True)

    def _ensure_numpy_index(self, force: bool = False):
        """Đảm bảo ma trận CSC + doc_ids/norms khớp doc_vectors hiện tại.
        Khi thêm/xoá 1 doc, đánh dấu dirty và build lại lười ở lần search kế tiếp
        (tránh rebuild O(N) sau mỗi lần tạo câu hỏi)."""
        if self.doc_matrix is None or force or self._matrix_dirty:
            t0 = time.perf_counter()
            self._build_numpy_index()
            self._matrix_dirty = False
            print(f"[Search] Numpy index sẵn sàng: {len(self.doc_ids)} docs "
                  f"({time.perf_counter() - t0:.1f}s)")
        if self._meta_arrays_dirty and self.doc_meta:
            self._rebuild_meta_arrays()

    def _build_numpy_index(self):
        """Xây ma trận CSC + mảng norm từ doc_vectors (chunked để hạn chế RAM)."""
        doc_ids = list(self.doc_vectors.keys())
        n = len(doc_ids)
        dim = max(self.dimension, 1)
        norms = np.zeros(n, dtype=np.float32)
        chunks = []
        per_chunk = 200_000
        for base in range(0, n, per_chunk):
            end = min(base + per_chunk, n)
            rows: list[int] = []
            cols: list[int] = []
            data: list[float] = []
            for i in range(base, end):
                vec, norm = self.doc_vectors[doc_ids[i]]
                norms[i] = norm
                if not vec:
                    continue
                rows.extend(vec.keys())
                cols.extend([i - base] * len(vec))
                data.extend(vec.values())
            if rows:
                chunks.append(scipy_sparse.csr_matrix(
                    (np.asarray(data, dtype=np.float32),
                     (np.asarray(rows, dtype=np.int32), np.asarray(cols, dtype=np.int32))),
                    shape=(dim, end - base),
                ))
            else:
                chunks.append(scipy_sparse.csr_matrix((dim, end - base), dtype=np.float32))
        self.doc_matrix = (scipy_sparse.hstack(chunks, format="csr") if chunks
                           else scipy_sparse.csr_matrix((dim, 0), dtype=np.float32))
        self.doc_ids = doc_ids
        self.doc_norms = norms
        self._rebuild_meta_arrays()

    def _rebuild_meta_arrays(self):
        """Mảng created_ts/vote_score/exists theo thứ tự doc_ids - dùng cho sort newest/votes."""
        n = len(self.doc_ids)
        created = np.zeros(n, dtype=np.float64)
        votes = np.zeros(n, dtype=np.float32)
        exists = np.zeros(n, dtype=bool)
        for i, qid in enumerate(self.doc_ids):
            meta = self.doc_meta.get(qid)
            if meta is not None:
                exists[i] = True
                created[i] = meta.created_ts
                votes[i] = meta.vote_score
        self.created_arr = created
        self.votes_arr = votes
        self.meta_exists = exists
        self._meta_arrays_dirty = False

    def _rebuild_inverted_index(self):
        inv: dict[int, list[str]] = {}
        for qid, (vec, _norm) in self.doc_vectors.items():
            for idx in vec:
                if idx not in inv:
                    inv[idx] = []
                inv[idx].append(qid)
        self.inverted_index = inv

    def add_to_inverted_index(self, qid: str, vec: dict[int, float]):
        """Thêm/cập nhật 1 document vào inverted index sau index_single_question."""
        # Xóa qid khỏi tất cả bucket cũ (O(unique_terms_old) - tối ưu đủ cho 1 doc)
        for bucket in self.inverted_index.values():
            try:
                bucket.remove(qid)
            except ValueError:
                pass
        # Ghi vào bucket mới
        for idx in vec:
            if idx not in self.inverted_index:
                self.inverted_index[idx] = []
            self.inverted_index[idx].append(qid)

    def remove_from_inverted_index(self, qid: str):
        for bucket in self.inverted_index.values():
            try:
                bucket.remove(qid)
            except ValueError:
                pass


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


def _fuzzy_match_token(token: str, cutoff: float = 0.72) -> str | None:
    """
    Tìm từ gần nhất trong vocab bằng binary search thay vì brute-force difflib.
    Chiến lược: lấy ~30 candidates quanh vị trí binary-search (prefix gần nhất),
    sau đó chỉ chạy SequenceMatcher trên tập nhỏ đó → O(log V + 30) thay vì O(V).
    """
    if not _cache.vocab_keys_sorted:
        return None
    keys = _cache.vocab_keys_sorted
    pos = bisect.bisect_left(keys, token)
    # Lấy window [-15, +15] quanh pos
    start = max(0, pos - 15)
    end = min(len(keys), pos + 15)
    candidates = keys[start:end]
    if not candidates:
        return None

    import difflib as _dl
    best_ratio = 0.0
    best_match = None
    sm = _dl.SequenceMatcher(autojunk=False)
    sm.set_seq1(token)
    for cand in candidates:
        sm.set_seq2(cand)
        r = sm.ratio()
        if r > best_ratio:
            best_ratio = r
            best_match = cand
    return best_match if best_ratio >= cutoff else None


def encode_query(query: str) -> tuple[dict[int, float], float]:
    tokens = preprocess(query)
    resolved_tokens = []

    for t in tokens:
        if t in _cache.vocab:
            resolved_tokens.append(t)
        else:
            # Fuzzy match dùng binary-search window thay vì difflib O(V)
            match = _fuzzy_match_token(t)
            if match:
                resolved_tokens.append(match)

    return _encode_tokens(resolved_tokens)


def cosine(vec_a: dict[int, float], norm_a: float, vec_b: dict[int, float], norm_b: float) -> float:
    if norm_a == 0 or norm_b == 0:
        return 0.0
    # Dot product qua giao 2 dict thưa - nhanh vì tiêu đề rất ngắn (thường < 15 token khác 0)
    small, big = (vec_a, vec_b) if len(vec_a) < len(vec_b) else (vec_b, vec_a)
    dot = sum(w * big[idx] for idx, w in small.items() if idx in big)
    return dot / (norm_a * norm_b)


async def _build_doc_meta_users():
    """Nạp metadata nhẹ của mọi câu hỏi + map user (authorId->name) vào RAM,
    phục vụ filter kiểu SO (tag/score/answers/accepted/user/created) không cần DB call."""
    users_map_local: dict[str, str] = {}
    try:
        async for u in users_col.find({}, {"displayName": 1, "username": 1}):
            name = (u.get("displayName") or u.get("username") or "").lower()
            if name:
                users_map_local[str(u["_id"])] = name
    except Exception:
        users_map_local = {}

    meta = {}
    projection = {
        "title": 1,
        "tags": 1,
        "voteScore": 1,
        "answerCount": 1,
        "acceptedAnswerId": 1,
        "createdAt": 1,
        "authorId": 1,
    }
    async for q in questions_col.find({}, projection):
        qid = str(q["_id"])
        try:
            created_ts = q.get("createdAt")
            created_ts = created_ts.timestamp() if created_ts is not None else 0.0
        except Exception:
            created_ts = 0.0
        meta[qid] = _DocMeta(
            title=(q.get("title") or "").lower(),
            tags=frozenset(q.get("tags", [])),
            vote_score=int(q.get("voteScore") or 0),
            answer_count=int(q.get("answerCount") or 0),
            has_accepted=bool(q.get("acceptedAnswerId")),
            created_ts=float(created_ts),
            author_name=users_map_local.get(str(q.get("authorId")), ""),
            author_id=str(q.get("authorId") or ""),
        )
    global users_map
    users_map.update(users_map_local)
    _cache.doc_meta = meta
    _cache._meta_arrays_dirty = True


users_map: dict[str, str] = {}

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
    # Build secondary indexes sau khi load xong
    _cache.rebuild_secondary_indexes()
    # Nạp metadata nhẹ (chú ý: với 1M câu hỏi việc này khá nặng, chạy 1 lần lúc khởi động)
    try:
        await _build_doc_meta_users()
    except Exception as _e:  # pragma: no cover - không làm gãy startup nếu metadata lỗi
        print(f"[Search] Cảnh báo: không nạp được doc_meta ({_e}); filter kiểu SO tạm bị tắt.")


async def reindex_all() -> dict:
    """
    Xây lại TOÀN BỘ vocabulary + vector từ đầu (dùng khi mới seed data, hoặc dataset đã
    tăng đáng kể - Phần 2.8.2 kế hoạch). Trả về thống kê thời gian để ghi log benchmark.
    Index cả Tiêu đề (nhân đôi trọng số) lẫn Nội dung chi tiết (Body) để tìm kiếm linh hoạt.

    Đã củng cố (hardening) để chống OOM / mất dữ liệu index khi dataset quy mô lớn:
      1. Ghi vector xuống MongoDB theo từng batch (streaming) thay vì gom toàn bộ
         doc_vector_writes vào RAM - cắt giảm bộ nhớ đáng kể với hàng triệu câu hỏi.
      2. Resumable: vocab version mới CHỈ được ghi sau khi đã ghi xong toàn bộ vector
         mới. Nếu bị gián đoạn giữa chừng, vocab cũ + vector cũ vẫn nguyên -> search
         vẫn hoạt động. Vector version cũ chỉ bị xóa sau khi version mới đã sẵn sàng.
      3. Post-check: so sánh số vector đã insert với số câu hỏi trước khi set cờ
         isIndexed, tránh trạng thái "có vocab nhưng thiếu vector" như đã từng gặp.
    """
    t0 = time.perf_counter()

    questions = [q async for q in questions_col.find({}, {"title": 1, "body": 1, "tags": 1})]
    if not questions:
        return {"indexed": 0, "elapsedMs": 0}

    preprocessed = [
        " ".join(preprocess(f"{q.get('title', '')} {q.get('title', '')} {q.get('body', '')} {' '.join(q.get('tags', []))}"))
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

    # Đọc version hiện hành từ DB (không dùng cache RAM của tiến trình) để tránh
    # reset về 1 khi reindex chạy trong tiến trình riêng (vd. script benchmark).
    current_vocab = await tfidf_vocabulary_col.find_one({"_id": VOCAB_DOC_ID})
    db_version = int(current_vocab["version"]) if current_vocab else 0
    new_version = db_version + 1
    vocab = {term: int(idx) for term, idx in vectorizer.vocabulary_.items()}
    idf = {str(i): float(w) for i, w in enumerate(vectorizer.idf_)}
    dimension = len(vocab)

    # --- 1) Ghi vector mới theo batch streaming (không giữ toàn bộ trong RAM) ---
    # Xóa các vector cùng version mới từ lần chạy trước (nếu có) để idempotent,
    # nhưng KHÔNG đụng tới dữ liệu version cũ đang được search.
    await question_vectors_tfidf_col.delete_many({"vocabVersion": new_version})

    batch_size = 50000
    new_doc_vectors: dict[str, tuple[dict, float]] = {}
    insert_count = 0
    total_questions = len(questions)
    for start in range(0, total_questions, batch_size):
        end = min(start + batch_size, total_questions)
        writes: list[dict] = []
        for i in range(start, end):
            q = questions[i]
            row = matrix[i]
            vector_sparse = {str(idx): float(val) for idx, val in zip(row.indices, row.data)}
            norm = float(np.sqrt(np.sum(row.data**2))) if row.data.size else 0.0
            writes.append(
                {
                    "questionId": q["_id"],
                    "vectorSparse": vector_sparse,
                    "norm": norm,
                    "vocabVersion": new_version,
                    "updatedAt": datetime.now(timezone.utc),
                }
            )
            new_doc_vectors[str(q["_id"])] = ({int(k): v for k, v in vector_sparse.items()}, norm)
        await question_vectors_tfidf_col.insert_many(writes)
        insert_count += len(writes)
        print(f"[Reindex] Đã ghi {insert_count}/{total_questions} vector TF-IDF...")

    # Post-check: chỉ tiếp tục khi ghi ĐỦ số vector
    if insert_count != total_questions:
        raise RuntimeError(
            f"[Reindex] ⚠ Thiếu vector: chỉ ghi được {insert_count}/{total_questions}"
            f" - hủy bỏ, giữ nguyên dữ liệu version cũ."
        )
    print(f"[Reindex] ✅ Đã ghi đủ {insert_count} vector TF-IDF.")

    # --- 2) Giờ mới quảng bá vocab/version mới (resumable) ---
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

    # --- 3) Dọn vector version cũ (chỉ sau khi version mới đã sẵn sàng) ---
    await question_vectors_tfidf_col.delete_many({"vocabVersion": {"$ne": new_version}})
    await questions_col.update_many({}, {"$set": {"isIndexed": True}})

    _cache.vocab = vocab
    _cache.idf = {int(k): v for k, v in idf.items()}
    _cache.dimension = dimension
    _cache.version = new_version
    _cache.doc_vectors = new_doc_vectors
    _cache.loaded = True
    # Rebuild secondary indexes (vocab_keys_sorted + inverted_index) sau reindex
    _cache.rebuild_secondary_indexes()
    # Nạp lại metadata nhẹ để filter kiểu SO hoạt động với dữ liệu mới
    try:
        await _build_doc_meta_users()
    except Exception as _e:
        print(f"[Reindex] Cảnh báo: không nạp được doc_meta ({_e})")

    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {"indexed": total_questions, "dimension": dimension, "version": new_version, "elapsedMs": round(elapsed_ms, 2)}

async def index_single_question(question_id, title: str, body: str = "", tags: list | None = None):
    """
    Re-index 1 câu hỏi bằng vocab HIỆN HÀNH (không retrain) - dùng khi tạo/sửa câu hỏi.
    Nếu chưa từng reindex_all() (chưa có vocab), bỏ qua - admin cần trigger reindex trước.
    """
    if not _cache.loaded or not _cache.vocab:
        return
    tag_text = " ".join(tags) if tags else ""
    full_text = f"{title} {title} {body} {tag_text}"
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
    qid_str = str(question_id)
    _cache.doc_vectors[qid_str] = (vec, norm)
    # Cập nhật inverted index cho câu hỏi vừa được index
    _cache.add_to_inverted_index(qid_str, vec)
    # Ma trận numpy trở nên lỗi thời - sẽ được build lười ở lần search kế tiếp
    _cache._matrix_dirty = True
    _cache._meta_arrays_dirty = True
    # Cập nhật metadata nhẹ (nếu đã có doc_meta) để filter kiểu SO không lệch
    try:
        fresh = await questions_col.find_one(
            {"_id": question_id},
            {"title": 1, "tags": 1, "voteScore": 1, "answerCount": 1,
             "acceptedAnswerId": 1, "createdAt": 1, "authorId": 1},
        )
        if fresh:
            created_ts = fresh.get("createdAt")
            created_ts = created_ts.timestamp() if created_ts is not None else 0.0
            author_name = users_map.get(str(fresh.get("authorId")), "")
            _cache.doc_meta[qid_str] = _DocMeta(
                title=(fresh.get("title") or "").lower(),
                tags=frozenset(fresh.get("tags", [])),
                vote_score=int(fresh.get("voteScore") or 0),
                answer_count=int(fresh.get("answerCount") or 0),
                has_accepted=bool(fresh.get("acceptedAnswerId")),
                created_ts=float(created_ts),
                author_name=author_name,
                author_id=str(fresh.get("authorId") or ""),
            )
    except Exception:
        pass


def get_stats() -> dict:
    return {"indexedCount": len(_cache.doc_vectors), "version": _cache.version, "dimension": _cache.dimension}


async def remove_question(question_id):
    """Dọn vector của 1 câu hỏi đã bị xóa - khỏi DB và khỏi cache RAM."""
    await question_vectors_tfidf_col.delete_one({"questionId": question_id})
    qid_str = str(question_id)
    _cache.doc_vectors.pop(qid_str, None)
    _cache.doc_meta.pop(qid_str, None)
    _cache.remove_from_inverted_index(qid_str)
    _cache._matrix_dirty = True
    _cache._meta_arrays_dirty = True


def _sort_scored(scored: list[tuple[str, float]], sort: str, top_k: int | None) -> list[tuple[str, float]]:
    """Sắp xếp theo kiểu SO rồi cắt top_k (nếu có). Dùng cho nhánh Python fallback."""
    if sort == "newest":
        scored.sort(key=lambda x: _cache.doc_meta[x[0]].created_ts if _cache.doc_meta.get(x[0]) else 0.0, reverse=True)
    elif sort == "votes":
        scored.sort(key=lambda x: _cache.doc_meta[x[0]].vote_score if _cache.doc_meta.get(x[0]) else 0, reverse=True)
    else:  # relevance
        scored.sort(key=lambda x: x[1], reverse=True)
    if top_k and top_k < len(scored):
        scored = scored[:top_k]
    return scored


def _search_numpy(
    q_vec: dict[int, float],
    q_norm: float,
    min_score: float,
    parsed: ParsedQuery,
    sort: str,
    user_id: str | None,
    has_filters: bool,
    top_k: int | None,
) -> tuple[list[tuple[str, float]], int]:
    """Fast-path: tính cosine với TOÀN BỘ docs bằng scipy sparse (C speed) thay vì
    vòng lặp Python từng doc. Trả về (top_k kết quả, tổng số kết quả đạt min_score)."""
    M = _cache.doc_matrix
    n = len(_cache.doc_ids)
    scores = np.zeros(n, dtype=np.float32)
    for idx, w in q_vec.items():
        row = M.getrow(idx)  # hàng = term, trải trên toàn bộ N doc (C speed)
        if row.nnz:
            scores += np.asarray(w * row.todense()).ravel()
    norms = _cache.doc_norms
    valid = norms > 0
    scores[valid] /= q_norm * norms[valid]
    scores[~valid] = 0.0

    passing_idx = np.nonzero(scores > min_score)[0]
    # Docs thiếu metadata bị loại (giữ đúng ngữ nghĩa của nhánh cũ khi doc_meta có dữ liệu)
    if _cache.doc_meta:
        passing_idx = passing_idx[_cache.meta_exists[passing_idx]]
    # Filter kiểu SO chỉ chạy khi query thực sự chứa filter - thay vì duyệt mọi doc như trước
    if has_filters:
        keep = []
        for i in passing_idx:
            qid = _cache.doc_ids[i]
            meta = _cache.doc_meta.get(qid)
            if meta is not None and _passes_filters(qid, meta, parsed, user_id):
                keep.append(i)
        passing_idx = np.asarray(keep, dtype=np.int64)

    total = int(len(passing_idx))
    if total == 0:
        return [], 0

    k = top_k if (top_k and top_k < total) else total
    if sort == "newest" or sort == "votes":
        key = _cache.created_arr if sort == "newest" else _cache.votes_arr
        if k < total:
            sel = passing_idx[np.argpartition(key[passing_idx], -k)[-k:]]
        else:
            sel = passing_idx
        sel = sel[np.argsort(-key[sel], kind="stable")]
    else:  # relevance
        if k < total:
            sel = passing_idx[np.argpartition(scores[passing_idx], -k)[-k:]]
        else:
            sel = passing_idx
        sel = sel[np.argsort(-scores[sel], kind="stable")]

    scored = [(_cache.doc_ids[i], float(scores[i])) for i in sel]
    return scored, total


def _search_python(
    q_vec: dict[int, float],
    q_norm: float,
    min_score: float,
    parsed: ParsedQuery,
    sort: str,
    user_id: str | None,
    has_filters: bool,
    top_k: int | None,
) -> tuple[list[tuple[str, float]], int]:
    """Nhánh fallback: duyệt candidate qua inverted index như bản cũ (dùng khi
    chưa build được ma trận numpy, vd. unit test với dữ liệu nhỏ)."""
    candidate_qids: set[str] = set()
    for idx in q_vec:
        bucket = _cache.inverted_index.get(idx)
        if bucket:
            candidate_qids.update(bucket)
    if not candidate_qids:
        return [], 0
    scored = []
    for qid in candidate_qids:
        entry = _cache.doc_vectors.get(qid)
        if entry is None:
            continue
        vec, norm = entry
        score = cosine(q_vec, q_norm, vec, norm)
        if score > min_score:
            scored.append((qid, score))
    if _cache.doc_meta:
        filtered = []
        for qid, score in scored:
            meta = _cache.doc_meta.get(qid)
            if meta is None:
                continue  # không có metadata -> bỏ (giữ đúng ngữ nghĩa bản cũ)
            if has_filters and not _passes_filters(qid, meta, parsed, user_id):
                continue
            filtered.append((qid, score))
        scored = filtered
    total = len(scored)
    return _sort_scored(scored, sort, top_k), total


def search(
    query: str,
    min_score: float = 0.0,
    parsed: ParsedQuery | None = None,
    sort: str = "relevance",
    user_id: str | None = None,
    top_k: int | None = None,
    return_total: bool = False,
):
    """
    Trả về [(questionId, score), ...] sau khi lọc & sắp xếp theo kiểu Stack Overflow.

    - `top_k`: nếu đặt, chỉ trả về top-K kết quả tốt nhất (phân trang ở tầng API vẫn
      hoạt động vì router truyền top_k = page * size). None = trả tất cả (hành vi cũ).
    - `return_total`: nếu True, trả về tuple (scored, total) với `total` là số kết quả
      đạt min_score sau filter - dùng để hiển thị phân trang mà không cần giữ full list.

    Đường đi: encode query -> cosine với toàn bộ index bằng scipy sparse (C speed)
    -> lọc/sắp xếp -> top-K. Với filter kiểu SO, chỉ duyệt các doc có score > min_score.
    """
    def _finish(scored: list[tuple[str, float]], total: int):
        return (scored, total) if return_total else scored

    if not _cache.vocab:
        return _finish([], 0)

    parsed = parsed or parse_query(query)
    # Quantitative terms dùng cho cosine (bỏ các keyword đặc biệt)
    q_text = " ".join(parsed.terms).strip()
    has_filters = bool(
        parsed.tags or parsed.phrases or parsed.exclude_terms
        or parsed.score_min is not None or parsed.score_max is not None
        or parsed.answers is not None or parsed.is_accepted is not None
        or parsed.user is not None or parsed.created_start is not None
        or parsed.created_end is not None
    )

    if q_text:
        q_vec, q_norm = encode_query(q_text)
        if q_norm == 0:
            return _finish([], 0)
        _cache._ensure_numpy_index()
        if _cache.doc_matrix is not None:
            scored, total = _search_numpy(q_vec, q_norm, min_score, parsed, sort, user_id, has_filters, top_k)
            return _finish(scored, total)
        scored, total = _search_python(q_vec, q_norm, min_score, parsed, sort, user_id, has_filters, top_k)
        return _finish(scored, total)

    # Không có text term nhưng có filter (vd chỉ "[docker]") -> duyệt toàn bộ doc_meta
    if not _cache.doc_meta or not has_filters:
        return _finish([], 0)
    scored = [
        (qid, 0.0)
        for qid in _cache.doc_meta
        if _passes_filters(qid, _cache.doc_meta[qid], parsed, user_id)
    ]
    scored = _sort_scored(scored, sort, top_k)
    return _finish(scored, len(scored))


def _passes_filters(qid: str, meta: _DocMeta, parsed: ParsedQuery, user_id: str | None) -> bool:
    """Kiểm tra 1 doc có thoả toàn bộ filter trong ParsedQuery không."""
    # Tag: phải có đủ mọi [tag] (AND)
    if parsed.tags and not all(t in meta.tags for t in parsed.tags):
        return False
    # Phrase: mọi cụm từ phải là substring của title (chuẩn hoá thường)
    if parsed.phrases and not all(p.lower() in meta.title for p in parsed.phrases):
        return False
    # Loại trừ term: dựa trên inverted index term -> nếu qid thuộc bucket term loại trừ -> bỏ
    if parsed.exclude_terms:
        exc_idx = {_cache.vocab[t] for t in parsed.exclude_terms if t in _cache.vocab}
        if exc_idx & set(_cache.doc_vectors[qid][0].keys()):
            return False
    # Score
    if parsed.score_min is not None and meta.vote_score < parsed.score_min:
        return False
    if parsed.score_max is not None and meta.vote_score > parsed.score_max:
        return False
    # Answers: 0 = chưa trả lời; N>0 = có ít nhất N câu trả lời
    if parsed.answers is not None:
        if parsed.answers == 0:
            if meta.answer_count != 0:
                return False
        elif meta.answer_count < parsed.answers:
            return False
    # is:accepted / is:unaccepted
    if parsed.is_accepted is not None and meta.has_accepted != parsed.is_accepted:
        return False
    # Created range (epoch seconds)
    if parsed.created_start is not None and meta.created_ts < parsed.created_start.timestamp():
        return False
    if parsed.created_end is not None and meta.created_ts > parsed.created_end.timestamp():
        return False
    # User: user:me -> khớp authorId với user đang đăng nhập
    if parsed.user is not None:
        if parsed.user == "__me__":
            if not user_id or meta.author_id != user_id:
                return False
        elif parsed.user and parsed.user not in meta.author_name:
            return False
    return True
