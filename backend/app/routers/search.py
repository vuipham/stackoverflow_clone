import time
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import questions_col, search_benchmark_log_col
from app.core.security import require_admin
from app.services.search import tfidf_service

router = APIRouter(tags=["search"])


async def _hydrate_results(scored: list[tuple[str, float]]) -> list[dict]:
    """Join questionId -> title/tags/preview để trả về Frontend, kèm điểm tương đồng (%)."""
    if not scored:
        return []
    ids = [ObjectId(qid) for qid, _ in scored]
    docs = {str(d["_id"]): d for d in await questions_col.find({"_id": {"$in": ids}}).to_list(length=len(ids))}
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
):
    """
    Tìm kiếm toàn bộ index TF-IDF và trả về TẤT CẢ kết quả liên quan (score > min_score),
    sau đó phân trang tại đây. Không giới hạn số lượng kết quả — giống Stack Overflow thật.
    """
    t0 = time.perf_counter()
    # Lấy TOÀN BỘ kết quả từ RAM cache (không giới hạn top_k)
    scored = tfidf_service.search(q, min_score=min_score)
    all_results = await _hydrate_results(scored)
    total = len(all_results)
    total_pages = max(1, (total + size - 1) // size)
    start = (page - 1) * size
    page_results = all_results[start : start + size]
    elapsed_ms = (time.perf_counter() - t0) * 1000
    await _log_benchmark("tfidf", q, elapsed_ms, total)
    return {
        "method": "tfidf",
        "query": q,
        "elapsedMs": round(elapsed_ms, 2),
        "results": page_results,
        "total": total,
        "page": page,
        "size": size,
        "totalPages": total_pages,
    }


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
