"""
Script tạo dataset câu hỏi lập trình quy mô lớn (10.000 - 1.000.000 câu hỏi)
KHÔNG BỊ TRÙNG LẶP (100% Unique Titles & Bodies) bằng thuật toán tổ hợp.

Chạy:
  ./venv/bin/python -m app.seed_massive_questions --count 1000000 --reset
"""
import argparse
import asyncio
import random
import sys
from datetime import datetime, timezone
from app.core.database import users_col, questions_col, tags_col

PREFIXES = [
    "Lỗi khi", "Cách tối ưu", "Hướng dẫn cấu hình", "Xử lý ngoại lệ",
    "Làm thế nào để", "So sánh", "Hướng dẫn cài đặt", "Tích hợp",
    "Khắc phục sự cố", "Phương pháp mở rộng", "Best practice cho",
    "Cách debug", "Hướng dẫn phân trang", "Thiết lập bảo mật cho",
    "Tối ưu bộ nhớ", "Xử lý concurrency cho", "Định cấu hình clustering",
    "Hướng dẫn mock test", "Tự động hóa deploy", "Cách caching",
    "Giải pháp load balancing", "Xử lý deadlock trong", "Phân quyền chi tiết cho",
    "Tối ưu truy vấn SQL", "Cách monitoring", "Viết middleware cho"
]

TECHS = [
    "FastAPI", "React 19", "Docker Container", "MongoDB 7.0", "Redis Cache",
    "PostgreSQL", "Apache Kafka", "Kubernetes", "Next.js 15", "Vue 3",
    "SvelteKit", "Node.js Express", "Spring Boot", "Golang Fiber", "Rust Actix",
    "Django REST", "GraphQL API", "gRPC Service", "Nginx", "RabbitMQ",
    "Elasticsearch", "Tailwind CSS", "TypeScript 5.5", "Python Asyncio", "AWS S3",
    "Terraform", "GitHub Actions", "Prometheus", "Grafana", "Celery Task Queue"
]

TOPICS = [
    "JWT Authentication", "TF-IDF Search Engine", "Websocket Connection",
    "Asyncio Event Loop", "GraphQL Schema", "Database Migration",
    "Microservice Architecture", "OAuth2 Single Sign-On", "Rate Limiting Middleware",
    "Distributed Locking", "Full-text Search Index", "Connection Pooling",
    "Memory Leak Debugging", "CORS Configuration", "SSL/TLS Certificate",
    "CI/CD Pipeline", "State Management", "Vector Similarity Search",
    "Background Worker", "Data Serialization", "Zero-downtime Deployment",
    "Horizontal Pod Autoscaling", "Cache Invalidation", "Sharding & Partitioning"
]

SCENARIOS = [
    "trên môi trường Production", "khi tải lượng lớn 100.000 req/s",
    "với mảng dữ liệu 1 triệu phần tử", "khi container bị OOMKilled",
    "trên hệ thống Ubuntu 24.04 LTS", "trong môi trường Kubernetes Cluster",
    "khi chạy trên AWS EC2 t3.medium", "với kiến trúc Serverless AWS Lambda",
    "khi nâng cấp từ phiên bản cũ", "khi kết nối qua mạng nội bộ VPN",
    "trải qua bài test stress-testing", "dưới tải trọng đọc ghi song song",
    "trong hệ thống ngân hàng thời gian thực", "khi triển khai trên hệ thống Multi-region"
]

DETAILS = [
    "bị treo memory leak không giải phóng", "trả về lỗi HTTP 500 Internal Server Error",
    "nhận kết quả response chậm > 2000ms", "gặp lỗi CORS preflight request",
    "bị văng exception ConnectionRefusedError", "xảy ra tình trạng CPU utilization 100%",
    "xuất hiện lỗi deadlock giữa các transaction", "không thể ghi log vào Elasticsearch",
    "khiến bộ nhớ RAM bị tràn vượt ngưỡng 8GB", "bị mất kết nối Websocket định kỳ mỗi 5 phút",
    "gặp lỗi JWT SignatureVerificationError", "không thể parse JSON payload dung lượng lớn"
]

TAG_POOL = [
    "python", "fastapi", "javascript", "react", "mongodb", "docker", "redis",
    "postgresql", "kubernetes", "vue", "svelte", "nodejs", "express", "go",
    "rust", "django", "graphql", "grpc", "nginx", "kafka", "elasticsearch",
    "typescript", "aws", "security", "jwt", "performance", "testing", "devops"
]


def generate_unique_question(seq_id: int) -> dict:
    p = random.choice(PREFIXES)
    t = random.choice(TECHS)
    top = random.choice(TOPICS)
    sc = random.choice(SCENARIOS)
    dt = random.choice(DETAILS)

    title = f"{p} {top} với {t} {sc} (#{seq_id})"
    body = (
        f"Tôi đang gặp vấn đề chuyên môn khi làm việc với **{t}** trong dự án.\n\n"
        f"**Mô tả kịch bản:**\n"
        f"Khi thực hiện {top} {sc}, hệ thống {dt}.\n\n"
        f"**Mã định danh vấn đề:** `#Q-ID-{seq_id:07d}`\n\n"
        f"Có giải pháp hoặc best practice nào để giải quyết dứt điểm vấn đề này không?"
    )
    num_tags = random.randint(2, 4)
    tags = list(set(random.sample(TAG_POOL, num_tags)))

    return {"title": title, "body": body, "tags": tags}


async def main():
    parser = argparse.ArgumentParser(description="Seed N câu hỏi không trùng lặp vào MongoDB.")
    parser.add_argument("--count", type=int, default=10000, help="Số lượng câu hỏi cần sinh (mặc định: 10,000)")
    parser.add_argument("--batch-size", type=int, default=10000, help="Kích thước batch ghi MongoDB (mặc định: 10000)")
    parser.add_argument("--reset", action="store_true", help="Xóa dữ liệu câu hỏi cũ trước khi nạp mới")
    args = parser.parse_args()

    users = [u async for u in users_col.find({})]
    if not users:
        print("❌ Chưa có user nào. Hãy chạy `make seed` trước để tạo user mẫu.")
        return

    if args.reset:
        print("🧹 Đã bật --reset: Đang xóa toàn bộ câu hỏi cũ trong MongoDB...")
        await questions_col.delete_many({})
        print("✅ Đã dọn sạch collection `questions`.")

    total_target = args.count
    batch_size = args.batch_size
    print(f"🚀 Bắt đầu sinh dataset {total_target:,} CÂU HỎI ĐỘC NHẤT (0% trùng lặp)...")

    # Tạo Unique Index cho title
    try:
        await questions_col.create_index("title", unique=True)
    except Exception:
        pass

    existing_count = await questions_col.count_documents({})
    print(f"📊 Số lượng câu hỏi hiện tại trong DB: {existing_count:,}")

    now = datetime.now(timezone.utc)
    docs = []
    inserted_total = 0
    start_time = datetime.now()

    for i in range(1, total_target + 1):
        seq_num = existing_count + i
        item = generate_unique_question(seq_num)
        author = random.choice(users)

        docs.append({
            "title": item["title"],
            "body": item["body"],
            "tags": item["tags"],
            "authorId": author["_id"],
            "viewCount": random.randint(5, 500),
            "voteScore": random.randint(-2, 25),
            "answerCount": 0,
            "acceptedAnswerId": None,
            "isIndexed": False,
            "createdAt": now,
            "updatedAt": now,
        })

        if len(docs) >= batch_size or i == total_target:
            res = await questions_col.insert_many(docs, ordered=False)
            inserted_total += len(res.inserted_ids)
            docs = []
            if inserted_total % 50000 == 0 or inserted_total == total_target:
                print(f"   ➜ Tiến độ: {inserted_total:,} / {total_target:,} câu hỏi ({inserted_total/total_target*100:.1f}%)...")

    elapsed = (datetime.now() - start_time).total_seconds()
    new_count = await questions_col.count_documents({})
    print(f"\n✅ THÀNH CÔNG HOÀN HẢO!")
    print(f"📈 Tổng số câu hỏi trong DB: {new_count:,}")
    print(f"⏱️  Thời gian sinh & chèn 1.000.000 câu hỏi: {elapsed:.2f} giây.")
    print("\n💡 Đừng quên reindex TF-IDF bằng lệnh: make reindex (hoặc bấm Reindex trên trang /admin)")


if __name__ == "__main__":
    asyncio.run(main())
