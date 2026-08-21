# Backend Python (FastAPI) — Hệ thống quản trị tri thức (Đề tài 3)

Đã code xong **Ngày 1–14 trong kế hoạch 3 tuần**:
- **Tuần 1 (nền tảng):** models MongoDB, auth (JWT), phân quyền reputation-gated đầy đủ
  (question, answer, comment, vote, tag, admin), dataset mẫu 400 câu hỏi.
- **Tuần 2 (Chức năng B - trọng tâm):** module tìm kiếm ngữ nghĩa **TF-IDF + SBERT**,
  cosine similarity, auto re-index, admin reindex/benchmark, script benchmark Precision@K.

## ✅ Đã kiểm thử thật
Toàn bộ logic (đăng ký, đăng nhập, CRUD question/answer/comment, vote, accept-answer,
cộng/trừ reputation, chặn theo ngưỡng đặc quyền, tag tự sinh, admin ban/chỉnh reputation,
cascade delete, **và cả pipeline search TF-IDF thật (reindex + search + benchmark log)**)
đã chạy test end-to-end với DB giả lập (`mongomock-motor`) — xem `app/dev_e2e_test.py`,
**42/42 test PASS**. Không phải chỉ kiểm tra cú pháp suông.

## Yêu cầu
- Python >= 3.10
- MongoDB đang chạy (local hoặc Atlas):
  ```bash
  docker run -d -p 27017:27017 --name mongo mongo:7
  ```
- (Tùy chọn nhưng cần cho SBERT) máy có kết nối Internet ở lần chạy đầu để tải model
  pretrained từ HuggingFace (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`,
  ~470MB). Nếu không có mạng / chưa cài `sentence-transformers`, **toàn bộ app vẫn chạy
  bình thường** — chỉ riêng `/api/search/sbert` sẽ trả lỗi 503, các phần khác (kể cả
  `/api/search/tfidf`) không bị ảnh hưởng.

## Cài đặt & chạy
```bash
cd backend-py
python3 -m venv venv
./venv/bin/pip install -r requirements.txt      # Linux/Mac
# venv\Scripts\pip install -r requirements.txt  # Windows

cp .env.example .env      # chỉnh MONGO_URI/JWT_SECRET nếu cần

./venv/bin/python -m app.seed                    # tạo admin + 6 tài khoản test
./venv/bin/python -m app.seed_questions           # nạp 400 câu hỏi mẫu (cho module search)
./venv/bin/uvicorn app.main:app --reload --port 8000
```
Mở http://localhost:8000/docs để xem Swagger UI tự động sinh ra — có thể test API ngay trên trình duyệt.

**Lưu ý quan trọng:** sau khi seed xong, phải gọi 1 lần API reindex để build vocabulary
TF-IDF + encode SBERT cho toàn bộ dữ liệu (chưa tự động, vì đây là thao tác nặng):
```bash
TOKEN="<token của user admin, lấy từ /api/auth/login>"
curl -X POST http://localhost:8000/api/admin/search/reindex -H "Authorization: Bearer $TOKEN"
```
Sau đó `/api/search/tfidf?q=...` và `/api/search/sbert?q=...` mới có dữ liệu để trả về.
Nếu chỉ muốn thử nhanh TF-IDF/benchmark mà chưa cần chạy `uvicorn`, có thể chạy thẳng:
```bash
./venv/bin/python -m app.benchmark_search   # tự reindex rồi in bảng Precision@5/@10 + thời gian
```

## Tài khoản test sau khi seed (mật khẩu chung: `Test@123`)
| username | reputation | Ghi chú |
|---|---|---|
| admin | 1 | isAdmin=true |
| newbie | 1 | Chỉ hỏi/trả lời được |
| voter | 20 | Upvote được (>=15) |
| commenter | 60 | Bình luận bài người khác được (>=50) |
| critic | 130 | Downvote được (>=125) |
| editor | 600 | Sửa bài người khác được (>=500) |
| veteran | 2200 | Xóa câu hỏi người khác được (>=2000) |

## Chạy lại bộ test end-to-end (không cần MongoDB thật)
```bash
./venv/bin/pip install mongomock mongomock-motor
./venv/bin/python -m app.dev_e2e_test
```
Bộ test tự dùng DB giả lập nên **không cần** cài `sentence-transformers`/`underthesea` để
chạy qua — phần SBERT sẽ tự báo "model chưa sẵn sàng" và bị bỏ qua an toàn, phần TF-IDF
chạy full pipeline thật (reindex + search bằng thuật toán TF-IDF thật, không mock).

## API tổng quan

### Auth
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`

### Questions / Answers / Comments / Votes
- `GET|POST /api/questions`, `GET|PUT|DELETE /api/questions/{id}`
- `GET|POST /api/questions/{id}/answers`, `PUT|DELETE /api/answers/{id}`, `POST /api/answers/{id}/accept`
- `GET|POST /api/comments`, `DELETE /api/comments/{id}`
- `POST /api/votes`

### Tags
- `GET /api/tags` (public) — `POST|PUT|DELETE /api/tags(/{id})` (Admin only)
- Tag cũng được **tự sinh** khi user gõ tag mới lúc đăng câu hỏi (hành vi thật của Stack Overflow)

### Admin
- `GET /api/admin/users`, `PATCH /api/admin/users/{id}/ban`, `PATCH /api/admin/users/{id}/reputation`

### Search (Chức năng B — trọng tâm)
- `GET /api/search/tfidf?q=...&top_k=10` — Vector Space Model cổ điển, cosine similarity thủ công
- `GET /api/search/sbert?q=...&top_k=10` — Sentence-BERT, cosine similarity trên embedding dense
- `POST /api/admin/search/reindex` (Admin) — retrain vocab TF-IDF + re-encode SBERT cho TOÀN BỘ dữ liệu
- `GET /api/admin/search/benchmark-log` (Admin) — log thời gian phản hồi các lượt search gần nhất

Cả 2 endpoint search trả kèm `similarityPercent` (điểm tương đồng %) để dễ giải thích khi demo/báo cáo.

## Test nhanh bằng curl

**1. Đăng nhập lấy token:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"newbie","password":"Test@123"}'
```

**2. Tạo câu hỏi:**
```bash
TOKEN="<dán token vào đây>"
curl -X POST http://localhost:8000/api/questions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Cách dùng cosine similarity trong tìm kiếm là gì?","body":"...","tags":["nlp","search"]}'
```

**3. Tìm kiếm ngữ nghĩa (sau khi đã reindex):**
```bash
curl "http://localhost:8000/api/search/tfidf?q=tim+kiem+ngu+nghia&top_k=5"
curl "http://localhost:8000/api/search/sbert?q=tim+kiem+ngu+nghia&top_k=5"
```

**4. Thử downvote bằng `newbie` (rep=1) → phải bị từ chối 403, rồi bằng `critic` (rep=130) → thành công** (xem `app/dev_e2e_test.py` để có kịch bản đầy đủ, gồm cả answer/comment/tag/admin/search).

## Cấu trúc thư mục
```
app/
  core/
    config.py         # đọc .env (bao gồm SBERT_MODEL_NAME)
    database.py        # kết nối Motor + collections + ensure_indexes()
    password.py         # hash/verify password bằng bcrypt trực tiếp
    privileges.py        # bảng ngưỡng PRIVILEGE + REPUTATION_DELTA
    security.py           # get_current_user, require_reputation, require_admin, check_owner_or_privilege
  models/             # Pydantic schemas (request/response) - question/answer/comment/tag/admin/user/vote
  routers/
    auth.py, questions.py, answers.py, comments.py, votes.py, tags.py, admin.py
    search.py            # /api/search/tfidf, /api/search/sbert, /api/admin/search/*
  services/
    reputation_service.py   # adjust_reputation() dùng chung
    tag_service.py           # đồng bộ tags collection khi tạo/sửa/xóa câu hỏi
    search/
      preprocess.py           # tiền xử lý văn bản cho TF-IDF (tokenize, bỏ stopword)
      tfidf_service.py         # build vocab, cache RAM, cosine thủ công (Vector Space Model)
      sbert_service.py          # load model pretrained, brute-force cosine trên embedding dense
  data/
    questions_dataset.json    # 400 tiêu đề mẫu đa chủ đề (Ngày 6)
  main.py               # entry point FastAPI - load cache search lúc khởi động (lifespan)
  seed.py                # tạo admin + tài khoản test
  seed_questions.py       # nạp 400 câu hỏi mẫu vào MongoDB
  benchmark_search.py      # script Precision@5/@10 + thời gian, TF-IDF vs SBERT (Ngày 18)
  dev_e2e_test.py           # bộ test end-to-end (dùng mongomock, không cần Mongo thật)
```

## Ghi chú kỹ thuật quan trọng

### Nền tảng (Tuần 1)
- Dùng `bcrypt` trực tiếp thay vì `passlib` — tránh lỗi tương thích `passlib` 1.7.4 với
  `bcrypt` >= 4.1 (`AttributeError: module 'bcrypt' has no attribute '__about__'`).
- `isIndexed: false` mặc định trên mỗi câu hỏi, tự động reset về `false` khi sửa title,
  và được set lại `true` ngay khi `index_single_question()` chạy xong (tự động ở
  `POST/PUT /api/questions`).
- Tag được tạo "hữu cơ" (upsert + tăng `questionCount`) mỗi khi có câu hỏi mới gắn tag đó -
  Admin chỉ cần vào sửa mô tả / xóa tag rác, không phải tạo tag trước.
- Xóa câu hỏi cascade: xóa luôn answer/comment/vote liên quan + vector chỉ mục TF-IDF/SBERT
  tương ứng, tránh dữ liệu mồ côi.

### Module search (Tuần 2 - Chức năng B)
- **TF-IDF**: dùng `sklearn.TfidfVectorizer(norm=None)` để giữ trọng số thô, tự tính `norm`
  riêng cho từng vector — đúng công thức `cosine = dot(a,b) / (norm_a * norm_b)` trong kế
  hoạch, thay vì để sklearn tự L2-normalize (nếu vậy `norm` luôn = 1, không đúng ý đồ lưu
  trữ trong `question_vectors_tfidf`). Toàn bộ vocab + vector cache trong RAM (`_cache`
  module-level) - không query lại MongoDB mỗi lần search.
- **SBERT**: KHÔNG tự train — dùng thẳng model pretrained multilingual
  (`paraphrase-multilingual-MiniLM-L12-v2`, phù hợp cho tiêu đề trộn tiếng Việt + thuật ngữ
  tiếng Anh). Model load 1 lần lúc khởi động (`get_model()` singleton), embedding cache
  thành 1 ma trận numpy đã L2-normalize để search bằng brute-force cosine (nhân ma trận) -
  đủ nhanh (<1s) với vài trăm đến vài nghìn câu hỏi. **Khi dataset > 5.000 câu hỏi**, thay
  bước brute-force này bằng MongoDB Atlas `$vectorSearch` (tạo Vector Search Index kiểu
  `knnVector` trên field `embedding`, xem Phần 2.8.3 kế hoạch) hoặc Qdrant HNSW — không cần
  đổi schema lưu trữ, chỉ đổi cách query trong `sbert_service.search()`.
- **Auto re-index**: mỗi lần tạo/sửa title câu hỏi, `index_single_question()` được gọi ngay
  (đồng bộ) cho cả 2 phương pháp, dùng vocab/model **hiện hành** (không retrain vocab TF-IDF
  ở bước này). Việc **retrain lại vocab** (khi dataset tăng đáng kể, đúng lưu ý Phần 2.8.2)
  là thao tác chủ động, chỉ Admin trigger qua `POST /api/admin/search/reindex`.
- **Benchmark**: `app/benchmark_search.py` tự reindex rồi chạy 15 câu truy vấn tự soạn, tính
  Precision@5/@10 bằng cách đối chiếu tag của kết quả trả về với tag "đúng" gán sẵn cho từng
  câu truy vấn (cách xấp xỉ khách quan cho dataset seed có gắn tag rõ ràng theo chủ đề). Kết
  quả in ra bảng + lưu vào `search_benchmark_log` (method=`benchmark_summary`) để dùng thẳng
  cho phần thực nghiệm trong báo cáo (Ngày 18–19).
- Toàn bộ route bảo vệ bằng `Depends()` của FastAPI — xem `require_reputation()`,
  `require_admin()`, `check_owner_or_privilege()` trong `core/security.py`.

## Đã kiểm chứng thật trong sandbox (không chỉ lý thuyết)
Đã chạy thử với dataset thật 400 câu hỏi (mongomock, không cần Mongo server) để xác nhận
pipeline TF-IDF hoạt động đúng: `reindex_all()` build vocab 185 chiều trong 43ms, sau đó
`search()` trả kết quả xếp hạng hợp lý cho các truy vấn như "lỗi React" (top-1: "Cách xử lý
lỗi memory leak trong React?" 53%), "docker deploy production" (top-1: "Có nên dùng Docker
cho dự án production không?" 58.4%), "cosine similarity" (top-1 75.4%).

## Việc tiếp theo (theo đúng kế hoạch)
- Tuần 3: tích hợp Frontend (trang list/detail/tạo câu hỏi, thanh tìm kiếm chọn
  TF-IDF/SBERT hiển thị % tương đồng), test toàn luồng, vẽ biểu đồ benchmark, viết báo cáo,
  làm slide + quay demo dự phòng.
- Optional nếu dư thời gian: badge, thông báo real-time, quên mật khẩu qua email (đã cắt
  giảm theo đúng Phần 6 kế hoạch — "làm 1 mình cần ưu tiên đúng trọng số điểm").
