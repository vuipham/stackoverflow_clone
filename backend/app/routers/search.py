import time
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import questions_col, search_benchmark_log_col
from app.core.security import require_admin, get_current_user_optional
from app.services.search import tfidf_service
from app.services.search.query_parser import parse_query

router = APIRouter(tags=["search"])


async def _hydrate_results(scored: list[tuple[str, float]]) -> list[dict]:
    """
    Join questionId -> title/tags/preview để trả về Frontend, kèm điểm tương đồng (%).
    Chỉ fetch đúng các fields cần thiết (projection) — không kéo body về.
    """
    if not scored:
        return []
    ids = [ObjectId(qid) for qid, _ in scored]
    # Projection: chỉ lấy fields cần hiển thị, bỏ body/markdown nặng
    projection = {"title": 1, "tags": 1, "voteScore": 1, "answerCount": 1, "acceptedAnswerId": 1, "createdAt": 1}
    docs = {
        str(d["_id"]): d
        for d in await questions_col.find(
            {"_id": {"$in": ids}}, projection
        ).to_list(length=len(ids))
    }
    results = []
    for qid, score in scored:
        q = docs.get(qid)
        if not q:
            continue
        results.append(
            {
                "questionId": qid,
                "title": q["title"],
                "tags": q.get("tags", []),
                "voteScore": q.get("voteScore", 0),
                "answerCount": q.get("answerCount", 0),
                "isAccepted": bool(q.get("acceptedAnswerId")),
                "createdAt": q["createdAt"].isoformat() if q.get("createdAt") else None,
                "similarityScore": round(score, 4),
                "similarityPercent": round(score * 100, 1),
            }
        )
    return results


async def _log_benchmark(method: str, query: str, elapsed_ms: float, result_count: int):
    await search_benchmark_log_col.insert_one(
        {"method": method, "query": query, "elapsedMs": round(elapsed_ms, 2), "resultCount": result_count}
    )


@router.get("/api/search/tfidf")
async def search_tfidf(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(15, ge=1, le=50),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    sort: str = Query("relevance", regex="^(relevance|newest|votes)$"),
    _user: dict | None = Depends(get_current_user_optional),
):
    """
    Tìm kiếm toàn bộ index TF-IDF với cú pháp kiểu Stack Overflow, sau đó phân trang.

    Cú pháp hỗ trợ (trong `q`):
      "cụm từ"        -> phrase khớp trong tiêu đề
      [tag]           -> lọc theo tag
      -term           -> loại trừ term
      score:5         -> score >= 5;  score:0-4 (range)
      answers:0       -> câu chưa có trả lời
      is:accepted     -> có accepted answer
      user:name       -> tác giả; user:me -> người đang đăng nhập
      created:2024-01-01..2024-06-30 -> khoảng thời gian tạo

    `sort`: relevance (cosine) | newest | votes.
    """
    t0 = time.perf_counter()
    parsed = parse_query(q)
    user_id = str(_user["_id"]) if _user else None
    # Lấy đúng top (page*size) kết quả từ RAM cache — chỉ ID + score, không có DB call.
    # Fast-path numpy trả kèm total chính xác để phân trang mà không cần sort toàn bộ.
    scored, total = tfidf_service.search(
        q, min_score=min_score, parsed=parsed, sort=sort, user_id=user_id,
        top_k=page * size, return_total=True,
    )
    total_pages = max(1, (total + size - 1) // size)
    start = (page - 1) * size
    # Cắt page TRƯỚC — chỉ hydrate đúng `size` kết quả cần trả về (mặc định 15)
    page_scored = scored[start : start + size]
    page_results = await _hydrate_results(page_scored)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    await _log_benchmark("tfidf", q, elapsed_ms, total)
    return {
        "method": "tfidf",
        "query": q,
        "sort": sort,
        "elapsedMs": round(elapsed_ms, 2),
        "results": page_results,
        "total": total,
        "page": page,
        "size": size,
        "totalPages": total_pages,
    }


@router.get("/api/questions/{question_id}/related")
async def related_questions(question_id: str, limit: int = Query(5, ge=1, le=10)):
    """
    Trả về tối đa `limit` câu hỏi liên quan dựa trên TF-IDF similarity với tiêu đề câu hỏi hiện tại.
    Không cần DB call để tính score — mọi thứ nằm trong RAM cache, chỉ cần hydrate top-K.
    """
    from app.core.database import questions_col as qcol
    from bson import ObjectId as OID
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID không hợp lệ")
    q = await qcol.find_one({"_id": OID(question_id)}, {"title": 1})
    if not q:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    scored, _total = tfidf_service.search(q["title"], min_score=0.05, top_k=limit + 1, return_total=True)
    # Lọc bỏ chính câu hỏi này
    scored = [(qid, score) for qid, score in scored if qid != question_id]
    top = scored[:limit]
    results = await _hydrate_results(top)
    return {"related": results}


@router.post("/api/admin/search/reindex")
async def trigger_reindex(_admin: dict = Depends(require_admin)):
    """
    Xây lại toàn bộ chỉ mục TF-IDF cho MỌI câu hỏi hiện có. Chỉ Admin được gọi - đây
    là thao tác nặng, không tự động chạy theo request thường (khác với
    index_single_question khi tạo/sửa 1 câu hỏi).
    """
    tfidf_result = await tfidf_service.reindex_all()
    return {"tfidf": tfidf_result}


@router.get("/api/admin/search/benchmark-log")
async def get_benchmark_log(limit: int = Query(50, ge=1, le=500), _admin: dict = Depends(require_admin)):
    """Xem log thời gian phản hồi gần nhất - dùng cho báo cáo (Ngày 14/18)."""
    cursor = search_benchmark_log_col.find({}).sort("_id", -1).limit(limit)
    logs = [{"method": l["method"], "query": l["query"], "elapsedMs": l["elapsedMs"], "resultCount": l["resultCount"]}
            async for l in cursor]
    return {"logs": logs}
