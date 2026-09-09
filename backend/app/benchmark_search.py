"""
Benchmark đánh giá chất lượng tìm kiếm TF-IDF: Precision@5, Precision@10, thời gian phản hồi.
Kết quả dùng thẳng cho báo cáo (Phần thực nghiệm).

Cách chấm "relevant": 1 kết quả được coi là relevant với truy vấn nếu tag `relevant_tag`
của truy vấn đó có trong `tags` của câu hỏi trả về - xấp xỉ khách quan, tự động hóa được.

Mặc định đo QUA HTTP API của backend đang chạy (end-to-end thật: network + hydrate + JSON,
không cần nạp 1M vector vào RAM của tiến trình benchmark -> tránh OOM).

Chạy:
  cd backend && venv/bin/python -m app.benchmark_search                # đo qua API (nhanh, an toàn RAM)
  cd backend && venv/bin/python -m app.benchmark_search --repeat 5     # mỗi query đo 5 lần lấy TB
  cd backend && venv/bin/python -m app.benchmark_search --reindex      # reindex TRƯỚC rồi mới đo (nặng ~4 phút)
"""
import argparse
import asyncio
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from app.core.database import search_benchmark_log_col

# 15 câu truy vấn tự soạn, đa dạng chủ đề, kèm tag "đúng" (thuộc bộ tag thật trong dataset)
# dùng để tính Precision@K
TEST_QUERIES = [
    {"query": "cách kết nối cơ sở dữ liệu MongoDB", "relevant_tag": "mongodb"},
    {"query": "lỗi khi dùng React trong dự án", "relevant_tag": "react"},
    {"query": "tối ưu hiệu năng Docker container", "relevant_tag": "docker"},
    {"query": "xác thực người dùng bằng JWT", "relevant_tag": "jwt"},
    {"query": "triển khai mô hình học máy bằng Python", "relevant_tag": "python"},
    {"query": "tối ưu hiệu năng cho hệ thống", "relevant_tag": "performance"},
    {"query": "so sánh Python với Node.js", "relevant_tag": "nodejs"},
    {"query": "thiết lập Kubernetes cluster", "relevant_tag": "kubernetes"},
    {"query": "viết unit test cho FastAPI", "relevant_tag": "fastapi"},
    {"query": "tìm kiếm toàn văn với Elasticsearch", "relevant_tag": "elasticsearch"},
    {"query": "bảo mật API với JWT token", "relevant_tag": "security"},
    {"query": "thiết lập pipeline CI/CD", "relevant_tag": "devops"},
    {"query": "deploy ứng dụng Django lên AWS", "relevant_tag": "django"},
    {"query": "sử dụng Redis để cache dữ liệu", "relevant_tag": "redis"},
    {"query": "xây dựng API với Express", "relevant_tag": "express"},
]

RESULT_JSON = Path(__file__).resolve().parent.parent.parent / "benchmark_result_tfidf.json"


def precision_at_k(results: list[dict], relevant_tag: str, k: int) -> float:
    top_k = results[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if relevant_tag in r.get("tags", []))
    return hits / len(top_k)


def call_api_with_retry(base_url: str, query: str, repeat: int, retries: int = 3) -> tuple[dict, list[float]]:
    """Đo 1 query `repeat` lần; mỗi lần lỗi mạng/timeout thì thử lại tối đa `retries` lần."""
    url = f"{base_url}/api/search/tfidf?q={urllib.parse.quote(query)}&page=1&size=10&min_score=0"
    times: list[float] = []
    data: dict = {}
    for _ in range(repeat):
        for attempt in range(retries + 1):
            try:
                t0 = time.perf_counter()
                with urllib.request.urlopen(url, timeout=180) as resp:
                    data = json.loads(resp.read())
                times.append((time.perf_counter() - t0) * 1000)
                break
            except Exception as exc:
                if attempt == retries:
                    raise
                print(f"    [warn] lỗi tạm thời ({exc.__class__.__name__}), thử lại lần {attempt + 2}...", flush=True)
                time.sleep(2)
    return data, times


def run_benchmark(base_url: str, repeat: int) -> tuple[list[dict], dict]:
    rows = []
    for i, tc in enumerate(TEST_QUERIES, 1):
        query, tag = tc["query"], tc["relevant_tag"]
        print(f"  [{i:>2}/{len(TEST_QUERIES)}] {query} ...", flush=True)
        data, times = call_api_with_retry(base_url, query, repeat)
        results = data.get("results", [])
        rows.append(
            {
                "query": query,
                "relevant_tag": tag,
                "client_ms": round(sum(times) / len(times), 2),
                "server_ms": data.get("elapsedMs", 0),
                "total_matches": data.get("total", 0),
                "p5": precision_at_k(results, tag, 5),
                "p10": precision_at_k(results, tag, 10),
            }
        )

    n = len(rows)
    summary = {
        "avgClientMs": round(sum(r["client_ms"] for r in rows) / n, 2),
        "avgServerMs": round(sum(r["server_ms"] for r in rows) / n, 2),
        "avgP5": round(sum(r["p5"] for r in rows) / n, 3),
        "avgP10": round(sum(r["p10"] for r in rows) / n, 3),
        "repeat": repeat,
        "base_url": base_url,
    }
    return rows, summary


def print_table(rows: list[dict], summary: dict) -> None:
    line = "-" * 104
    print("\n" + "=" * 104)
    print(f"{'Query':<44} {'Tag đúng':<15} {'Client ms':>9} {'Server ms':>9} {'Kết quả':>8} {'P@5':>5} {'P@10':>5}")
    print(line)
    for r in rows:
        print(
            f"{r['query'][:44]:<44} {r['relevant_tag']:<15} {r['client_ms']:>9.2f} {r['server_ms']:>9.2f}"
            f" {r['total_matches']:>8} {r['p5']:>5.2f} {r['p10']:>5.2f}"
        )
    print(line)
    print(
        f"{'TRUNG BÌNH':<44} {'':<15} {summary['avgClientMs']:>9.2f} {summary['avgServerMs']:>9.2f}"
        f" {'':>8} {summary['avgP5']:>5.2f} {summary['avgP10']:>5.2f}"
    )
    print("=" * 104)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark TF-IDF qua HTTP API của backend.")
    parser.add_argument("--api", default="http://localhost:8000", help="Base URL backend (mặc định localhost:8000)")
    parser.add_argument("--repeat", type=int, default=3, help="Số lần đo mỗi query (lấy trung bình, mặc định 3)")
    parser.add_argument("--reindex", action="store_true", help="Reindex toàn bộ TRƯỚC khi đo (nặng ~4 phút + ~16GB RAM)")
    args = parser.parse_args()

    if args.reindex:
        from app.services.search import tfidf_service

        print("[Benchmark] Đang reindex toàn bộ (nặng, ~4 phút)...")
        stats = await tfidf_service.reindex_all()
        print(f"[Benchmark] Reindex xong: {stats}")

    print(f"[Benchmark] Đo {len(TEST_QUERIES)} query x {args.repeat} lần qua {args.api} ...")
    rows, summary = run_benchmark(args.api, args.repeat)
    print_table(rows, summary)

    out = {"summary": summary, "rows": rows}
    RESULT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[Benchmark] Đã lưu kết quả vào {RESULT_JSON}")
    await search_benchmark_log_col.insert_one({"method": "benchmark_summary", "summary": summary, "rows": rows})
    print("[Benchmark] Kết quả đã lưu vào collection `search_benchmark_log` (xem lại tại trang /admin).")


if __name__ == "__main__":
    asyncio.run(main())
