from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import ensure_indexes
from app.routers import auth, questions, votes, answers, comments, tags, admin, search
from app.services.search import tfidf_service, sbert_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    print("[DB] Đã tạo/xác nhận index MongoDB")

    # Nạp cache RAM cho module search (Phần 4 - chiến lược <1s): đọc vocab/vector đã lưu
    # từ lần reindex trước đó (nếu có) - không load lại từ đầu mỗi lần search.
    await tfidf_service.load_cache_from_db()
    print(f"[Search] TF-IDF cache: {tfidf_service.get_stats()}")

    # Model SBERT load 1 lần, giữ RAM suốt vòng đời service (Phần 4). Nếu môi trường chưa
    # tải được model (không có mạng), app vẫn khởi động bình thường - chỉ /api/search/sbert lỗi.
    sbert_service.get_model()
    await sbert_service.load_cache_from_db()
    print(f"[Search] SBERT cache: {sbert_service.get_stats()}")

    yield


app = FastAPI(title="Knowledge Hub API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only - siết lại domain cụ thể khi deploy thật
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(questions.router)
app.include_router(votes.router)
app.include_router(answers.router)
app.include_router(comments.router)
app.include_router(tags.router)
app.include_router(admin.router)
app.include_router(search.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
