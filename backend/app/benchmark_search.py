"""
Benchmark so sánh TF-IDF vs SBERT: Precision@5, Precision@10, thời gian phản hồi.
Kết quả dùng thẳng cho báo cáo (Phần thực nghiệm) - Ngày 18-19 kế hoạch.

Cách chấm "relevant": vì dataset seed (`seed_questions.py`) có gắn tag rõ ràng theo chủ đề,
1 kết quả được coi là relevant với truy vấn nếu tag `relevant_tag` của truy vấn đó có trong
`tags` của câu hỏi trả về - đây là cách xấp xỉ khách quan, tự động hóa được cho bộ truy vấn
tự soạn (không cần gán nhãn tay từng cặp query-question).

Yêu cầu: đã chạy `python -m app.seed_questions` (có dữ liệu) và MongoDB đang chạy thật
(không dùng mongomock ở đây, vì cần chạy được sentence-transformers).

Chạy: python -m app.benchmark_search
"""
import asyncio
import time

from app.core.database import search_benchmark_log_col
from app.services.search import tfidf_service, sbert_service

# 15 câu truy vấn tự soạn, đa dạng chủ đề, kèm tag "đúng" dùng để tính Precision@K
TEST_QUERIES = [
    {"query": "cách kết nối cơ sở dữ liệu MongoDB", "relevant_tag": "mongodb"},
    {"query": "lỗi khi dùng React trong dự án", "relevant_tag": "react"},
    {"query": "tối ưu hiệu năng Docker container", "relevant_tag": "docker"},
    {"query": "xác thực người dùng bằng JWT", "relevant_tag": "jwt"},
    {"query": "triển khai mô hình học máy", "relevant_tag": "machine-learning"},
    {"query": "xử lý ngôn ngữ tự nhiên tiếng Việt", "relevant_tag": "nlp"},
    {"query": "so sánh Python với Node.js", "relevant_tag": "python"},
    {"query": "thiết lập Kubernetes cluster", "relevant_tag": "kubernetes"},
    {"query": "viết unit test cho FastAPI", "relevant_tag": "fastapi"},
    {"query": "tìm kiếm vector bằng Qdrant", "relevant_tag": "qdrant"},
    {"query": "tính độ tương đồng cosine similarity", "relevant_tag": "cosine-similarity"},
    {"query": "cấu hình CI/CD với GitHub Actions", "relevant_tag": "github-actions"},
    {"query": "deploy ứng dụng Django lên AWS", "relevant_tag": "django"},
    {"query": "sử dụng Redis để cache dữ liệu", "relevant_tag": "redis"},
    {"query": "xây dựng REST API chuẩn", "relevant_tag": "rest-api"},
]


def precision_at_k(results: list[dict], relevant_tag: str, k: int) -> float:
    top_k = results[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if relevant_tag in r.get("tags", []))
    return hits / len(top_k)


async def hydrate(scored):
    from app.routers.search import _hydrate_results

    return await _hydrate_results(scored)


async def run():
    print("[Benchmark] Đảm bảo chỉ mục là mới nhất - đang reindex toàn bộ...")
    tfidf_stats = await tfidf_service.reindex_all()
    sbert_stats = await sbert_service.reindex_all()
    print(f"[Benchmark] TF-IDF reindex: {tfidf_stats}")
    print(f"[Benchmark] SBERT reindex: {sbert_stats}")

    if sbert_service.get_model() is None:
        print("[Benchmark] CẢNH BÁO: model SBERT không sẵn sàng - bỏ qua phần SBERT.")

    rows = []
    for tc in TEST_QUERIES:
        query, tag = tc["query"], tc["relevant_tag"]

        t0 = time.perf_counter()
        tfidf_scored = tfidf_service.search(query, top_k=10)
        tfidf_ms = (time.perf_counter() - t0) * 1000
        tfidf_results = await hydrate(tfidf_scored)

        row = {
            "query": query,
            "tfidf_ms": round(tfidf_ms, 2),
            "tfidf_p5": precision_at_k(tfidf_results, tag, 5),
            "tfidf_p10": precision_at_k(tfidf_results, tag, 10),
        }

        if sbert_service.get_model() is not None:
            t0 = time.perf_counter()
            sbert_scored = sbert_service.search(query, top_k=10)
            sbert_ms = (time.perf_counter() - t0) * 1000
            sbert_results = await hydrate(sbert_scored)
            row.update(
                {
                    "sbert_ms": round(sbert_ms, 2),
                    "sbert_p5": precision_at_k(sbert_results, tag, 5),
                    "sbert_p10": precision_at_k(sbert_results, tag, 10),
                }
            )
        rows.append(row)

    print("\n" + "=" * 100)
    header = f"{'Query':<45} {'TF-IDF ms':>10} {'P@5':>6} {'P@10':>6} | {'SBERT ms':>10} {'P@5':>6} {'P@10':>6}"
    print(header)
    print("-" * 100)
    for r in rows:
        print(
            f"{r['query'][:45]:<45} {r['tfidf_ms']:>10.2f} {r['tfidf_p5']:>6.2f} {r['tfidf_p10']:>6.2f} | "
            f"{r.get('sbert_ms', 0):>10.2f} {r.get('sbert_p5', 0):>6.2f} {r.get('sbert_p10', 0):>6.2f}"
        )

    n = len(rows)
    avg_tfidf_ms = sum(r["tfidf_ms"] for r in rows) / n
    avg_tfidf_p5 = sum(r["tfidf_p5"] for r in rows) / n
    avg_tfidf_p10 = sum(r["tfidf_p10"] for r in rows) / n
    print("-" * 100)
    print(f"{'TRUNG BÌNH':<45} {avg_tfidf_ms:>10.2f} {avg_tfidf_p5:>6.2f} {avg_tfidf_p10:>6.2f}", end="")

    summary = {
        "tfidf": {"avgMs": round(avg_tfidf_ms, 2), "avgP5": round(avg_tfidf_p5, 3), "avgP10": round(avg_tfidf_p10, 3)}
    }
    if sbert_service.get_model() is not None:
        avg_sbert_ms = sum(r["sbert_ms"] for r in rows) / n
        avg_sbert_p5 = sum(r["sbert_p5"] for r in rows) / n
        avg_sbert_p10 = sum(r["sbert_p10"] for r in rows) / n
        print(f" | {avg_sbert_ms:>10.2f} {avg_sbert_p5:>6.2f} {avg_sbert_p10:>6.2f}")
        summary["sbert"] = {
            "avgMs": round(avg_sbert_ms, 2), "avgP5": round(avg_sbert_p5, 3), "avgP10": round(avg_sbert_p10, 3)
        }
    else:
        print()
    print("=" * 100)

    await search_benchmark_log_col.insert_one({"method": "benchmark_summary", "summary": summary, "rows": rows})
    print("\n[Benchmark] Đã lưu kết quả vào collection `search_benchmark_log` (method=benchmark_summary) để đưa vào báo cáo.")


if __name__ == "__main__":
    asyncio.run(run())
