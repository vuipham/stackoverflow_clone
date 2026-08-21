# ĐỀ TÀI 3: HỆ THỐNG QUẢN TRỊ TRI THỨC (Stack Overflow Clone + Semantic Search)
*(Phiên bản: làm cá nhân 1 mình — tập trung trọng tâm vào chức năng đặc thù B)*

## PHẦN 1: PHÂN TÍCH ĐỀ TÀI

### 1.1. Mục tiêu
Xây dựng hệ thống hỏi–đáp tri thức (kiểu Stack Overflow), trong đó **trọng tâm chấm điểm và trọng tâm thời gian** dồn vào module tìm kiếm ngữ nghĩa theo tiêu đề dùng Vector Space Model. Các chức năng nền tảng (CRUD câu hỏi/trả lời, vote, tag...) được làm ở mức **đủ dùng, không lan man**, vì làm một mình cần ưu tiên đúng trọng số điểm.

### 1.2. Phạm vi chức năng

**A. Chức năng nền tảng (làm gọn, đủ để hệ thống chạy được và có dữ liệu cho phần B)**
- Đăng ký / đăng nhập (JWT) + **phân quyền theo điểm uy tín (reputation-gated privileges) — đúng cơ chế thực tế của Stack Overflow**
- CRUD câu hỏi (tiêu đề, nội dung, tag)
- CRUD câu trả lời, bình luận đơn giản
- Upvote/downvote — **có cộng/trừ reputation thật sự** (không chỉ đếm số vote suông), vì reputation chính là "chìa khóa" mở quyền
- Quản lý tag, lọc theo tag
- 1 tài khoản **Admin** cố định (không qua reputation) để quản trị hệ thống — vì ở SO thật, Admin là nhân viên công ty chứ không mở bằng điểm

**Bảng đặc quyền theo Reputation (rút gọn từ mô hình thật của Stack Overflow, đủ cho phạm vi đồ án):**
| Reputation | Đặc quyền mở ra |
|---|---|
| 1 (mặc định khi đăng ký) | Đặt câu hỏi, trả lời câu hỏi |
| 15 | Upvote |
| 50 | Bình luận vào bài của **người khác** (dưới 50 chỉ bình luận được bài của chính mình) |
| 125 | Downvote |
| 500 | Sửa bài viết của **người khác** trực tiếp |
| 2000 | Xóa/khôi phục câu hỏi của người khác |

**Cơ chế cộng/trừ reputation (mô phỏng đúng SO):**
| Sự kiện | Thay đổi reputation |
|---|---|
| Câu hỏi/câu trả lời của bạn được upvote | +10 |
| Câu trả lời của bạn được chấp nhận (accepted) | +15 |
| Câu hỏi/câu trả lời của bạn bị downvote | −2 |
| Bạn chủ động downvote người khác | −1 (chi phí downvote, đúng như SO thật) |

**Vai trò Admin (ngoài cơ chế reputation):**
| Hành động | Điều kiện |
|---|---|
| Quản lý user (khóa tài khoản, chỉnh reputation thủ công) | Chỉ Admin |
| Quản lý tag (tạo/sửa/xóa) | Chỉ Admin |
| Trigger re-index thủ công / xem log benchmark search | Chỉ Admin |

**B. Chức năng đặc thù — TRỌNG TÂM (chiếm phần lớn thời gian và điểm số)**
1. Tìm kiếm câu hỏi theo tiêu đề bằng từ khóa (semantic/vector search, không phải LIKE)
2. Xây dựng vector chỉ mục cho tiêu đề — **cài đặt cả 2 phương pháp**:
   - TF-IDF (Vector Space Model cổ điển)
   - Sentence-BERT (embedding ngữ nghĩa)
3. Lưu trữ vector chỉ mục vào MongoDB (Atlas Vector Search) hoặc Vector DB (Qdrant)
4. Đo độ tương đồng bằng Cosine Similarity, trả về top-K, có benchmark so sánh 2 phương pháp

### 1.3. Yêu cầu phi chức năng
- Thời gian phản hồi tìm kiếm **< 1 giây** (xem chiến lược tối ưu ở Phần 4)
- Hệ thống re-index được khi có câu hỏi mới/sửa/xóa
- Giao diện tối giản nhưng rõ ràng, đủ để demo luồng: tạo câu hỏi → tìm kiếm → xem kết quả xếp hạng theo độ tương đồng

### 1.4. Công nghệ sử dụng
| Thành phần | Lựa chọn |
|---|---|
| Backend | **Python (FastAPI)** — dùng chung 1 ngôn ngữ cho cả API chính lẫn phần xử lý vector (TF-IDF/SBERT), khỏi cần tách microservice riêng như bản kế hoạch trước → kiến trúc gọn hơn |
| Driver MongoDB | Motor (async) hoặc PyMongo (sync) |
| Auth | PyJWT + passlib (hash password) |
| Xử lý vector | scikit-learn (`TfidfVectorizer`), sentence-transformers (SBERT) |
| Frontend | **Svelte** (SvelteKit hoặc Svelte + Vite thuần) |
| Gọi API | `fetch` trong Svelte store, hoặc thư viện `axios` |

> Vì backend và phần search giờ cùng là Python, có thể gộp thành **1 service FastAPI duy nhất** (routers tách theo module: `auth`, `questions`, `votes`, `search`) thay vì 2 service riêng như thiết kế Node.js trước đó — đỡ 1 tầng gọi HTTP nội bộ, cũng dễ deploy hơn khi làm một mình.

---

## PHẦN 2: THIẾT KẾ CƠ SỞ DỮ LIỆU (MongoDB)

### 2.1. Nguyên tắc thiết kế
- Dùng MongoDB (NoSQL, document-based), embedding vừa phải + reference cho phần dễ tăng trưởng (answers, comments) để tránh document quá lớn.
- Tách riêng collection lưu **vector chỉ mục** khỏi collection `questions` để: (a) dễ re-index độc lập, (b) không làm phình document chính, (c) dễ chuyển sang Vector DB riêng sau này mà không đụng schema chính.
- Với TF-IDF, phải lưu thêm **vocabulary/IDF toàn cục** vì khi có câu hỏi mới hoặc câu truy vấn mới, cần encode bằng đúng không gian từ vựng đã học lúc xây chỉ mục.

### 2.2. Collection: `users`
```json
{
  "_id": ObjectId,
  "username": "string, unique",
  "email": "string, unique",
  "passwordHash": "string",
  "displayName": "string",
  "isAdmin": false,          // <-- cờ Admin duy nhất, KHÔNG phải "role" nhiều bậc — gán tay/seed, không mở qua reputation
  "isBanned": false,
  "reputation": 1,           // mặc định 1 khi đăng ký, đúng như SO thật
  "reputationLog": [         // (tùy chọn) lưu lịch sử biến động để giải trình trong báo cáo/demo
    { "delta": 10, "reason": "upvote_received", "refId": ObjectId, "at": ISODate }
  ],
  "createdAt": ISODate
}
```
Index: `db.users.createIndex({ reputation: -1 })` (phục vụ trang xếp hạng user nếu cần), `db.users.createIndex({ isAdmin: 1 })`.

**Cài đặt phân quyền reputation-gated (backend):**
- Payload JWT chứa `{ userId, reputation, isAdmin }` (hoặc chỉ `userId` rồi mỗi request query lại `reputation` mới nhất từ DB — **nên chọn cách này** vì reputation thay đổi liên tục, JWT cache số cũ dễ gây sai lệch quyền).
- Bảng ngưỡng đặc quyền định nghĩa dạng hằng số dùng chung:
  ```js
  const PRIVILEGE = {
    ASK_ANSWER: 1, UPVOTE: 15, COMMENT_ON_OTHERS: 50,
    DOWNVOTE: 125, EDIT_OTHERS_POST: 500, DELETE_OTHERS_QUESTION: 2000
  };
  ```
- Middleware `requireReputation(threshold)`: lấy `req.user.reputation` (query MongoDB) → so sánh với `threshold`, không đủ thì trả 403 kèm thông báo "Cần tối thiểu X điểm reputation để thực hiện hành động này" (đúng UX thật của SO, tăng tính thuyết phục khi demo).
- Middleware `requireOwnerOrPrivilege(threshold)`: cho phép nếu `req.user.id === resource.authorId` **hoặc** `req.user.reputation >= threshold` — dùng chung cho sửa/xóa question, answer, comment.
- Route quản trị hệ thống (user, tag, re-index) chỉ áp `requireAdmin` (kiểm tra `isAdmin === true`), tách biệt hoàn toàn khỏi cơ chế reputation.
- Hàm `adjustReputation(userId, delta, reason, refId)` được gọi mỗi khi có vote/accept-answer, cập nhật `reputation` + ghi vào `reputationLog` — nên viết thành 1 service dùng chung, gọi lại ở nhiều nơi (vote question, vote answer, accept answer).

### 2.3. Collection: `tags`
```json
{
  "_id": ObjectId,
  "name": "string, unique, lowercase",   // vd "mongodb", "react"
  "description": "string",
  "questionCount": 0
}
```

### 2.4. Collection: `questions` (bảng lõi — nguồn của dữ liệu cần vector hóa)
```json
{
  "_id": ObjectId,
  "title": "string",              // <-- trường được vector hóa cho search
  "body": "string",
  "tags": ["string"],             // denormalize tên tag để query nhanh
  "authorId": ObjectId,           // ref -> users
  "viewCount": 0,
  "voteScore": 0,                 // cache = upvote - downvote
  "answerCount": 0,
  "acceptedAnswerId": ObjectId | null,
  "isIndexed": false,             // <-- cờ báo đã có vector hay chưa (dùng khi re-index)
  "createdAt": ISODate,
  "updatedAt": ISODate
}
```
Index cần tạo: `db.questions.createIndex({ tags: 1 })`, `{ createdAt: -1 }`, `{ isIndexed: 1 }`.

### 2.5. Collection: `answers`
```json
{
  "_id": ObjectId,
  "questionId": ObjectId,   // ref -> questions
  "authorId": ObjectId,
  "body": "string",
  "voteScore": 0,
  "isAccepted": false,
  "createdAt": ISODate
}
```

### 2.6. Collection: `comments`
```json
{
  "_id": ObjectId,
  "targetType": "question" | "answer",
  "targetId": ObjectId,
  "authorId": ObjectId,
  "content": "string",
  "createdAt": ISODate
}
```

### 2.7. Collection: `votes`
```json
{
  "_id": ObjectId,
  "userId": ObjectId,
  "targetType": "question" | "answer",
  "targetId": ObjectId,
  "value": 1 | -1,
  "createdAt": ISODate
}
```
Unique compound index: `{ userId: 1, targetType: 1, targetId: 1 }` để 1 user chỉ vote 1 lần/đối tượng.

---

### 2.8. Collection dành riêng cho Chức năng B (quan trọng nhất)

#### 2.8.1. `question_vectors_tfidf`
Lưu vector TF-IDF của từng tiêu đề — dùng dạng **sparse** (chỉ lưu index/term có giá trị ≠ 0) để tiết kiệm dung lượng và tăng tốc.
```json
{
  "_id": ObjectId,
  "questionId": ObjectId,        // ref -> questions, unique
  "vectorSparse": {              // dạng sparse: term_index -> tfidf_weight
    "12": 0.42,
    "87": 0.31,
    "203": 0.55
  },
  "norm": 0.774,                 // độ dài vector (để tính cosine nhanh: dot / (norm_a * norm_b))
  "vocabVersion": 3,             // <-- khớp với version của vocabulary tại thời điểm encode
  "updatedAt": ISODate
}
```

#### 2.8.2. `tfidf_vocabulary` (bảng phụ trợ bắt buộc phải có cho TF-IDF)
```json
{
  "_id": "current",              // document duy nhất, hoặc versioned
  "version": 3,
  "vocab": { "mongodb": 12, "search": 87, "vector": 203, ... },  // term -> index
  "idf": { "12": 2.1, "87": 1.8, "203": 3.4, ... },              // term_index -> idf weight
  "dimension": 512,
  "trainedAt": ISODate
}
```
> Lý do cần bảng này: TF-IDF không "tự sinh" vector cho 1 câu đơn lẻ — nó cần biết IDF của toàn tập để encode câu truy vấn hoặc câu hỏi mới **cùng không gian** với các vector đã lưu. Khi tập dữ liệu tăng đáng kể, cần re-train và tăng `version`, đồng thời re-encode toàn bộ `question_vectors_tfidf` (batch job).

#### 2.8.3. `question_vectors_sbert`
Vector SBERT là **dense** (không thưa), nên lưu dạng mảng số bình thường — đây cũng là dạng phù hợp để đưa vào Vector DB / MongoDB Atlas Vector Search index.
```json
{
  "_id": ObjectId,
  "questionId": ObjectId,     // ref -> questions, unique
  "embedding": [0.0123, -0.045, 0.221, ...],  // 384 hoặc 768 chiều tùy model
  "modelName": "all-MiniLM-L6-v2",
  "dimension": 384,
  "updatedAt": ISODate
}
```
Nếu dùng **MongoDB Atlas Vector Search**: tạo Vector Search Index trên field `embedding` (kiểu `knnVector`, similarity: `cosine`, dimensions: 384) → truy vấn bằng `$vectorSearch` thay vì tự viết cosine tay, đây là cách đạt yêu cầu <1s ổn định nhất.

Nếu dùng **Qdrant** (Vector DB riêng): collection Qdrant tương ứng lưu `payload = { questionId }` + `vector`, MongoDB chỉ giữ dữ liệu gốc — kiến trúc 2 CSDL song song.

---

## PHẦN 3: THIẾT KẾ LUỒNG XỬ LÝ CHỨC NĂNG B (chi tiết)

**Luồng Index (khi tạo/sửa câu hỏi):**
1. Câu hỏi được lưu vào `questions`, `isIndexed = false`
2. Background job/worker lấy `title` → tiền xử lý (lowercase, tokenize, bỏ stopword, stemming nếu tiếng Anh / hoặc dùng underthesea nếu tiếng Việt)
3. Sinh vector TF-IDF (dựa trên `tfidf_vocabulary` hiện hành) → lưu vào `question_vectors_tfidf`
4. Sinh vector SBERT (model đã load sẵn trong RAM) → lưu vào `question_vectors_sbert`
5. Cập nhật `questions.isIndexed = true`

**Luồng Search (khi user gõ từ khóa):**
1. Nhận query string từ Frontend
2. Tiền xử lý y hệt bước index
3. **Nhánh TF-IDF:** encode query bằng `tfidf_vocabulary` hiện hành → lấy toàn bộ `question_vectors_tfidf` (hoặc subset lọc trước theo tag nếu có filter) → tính cosine = dot(query, doc) / (norm_query * norm_doc) → sắp xếp giảm dần → top-K
4. **Nhánh SBERT:** encode query bằng SBERT model → gọi `$vectorSearch` (Atlas) hoặc Qdrant search API (ANN, HNSW index) → top-K kèm điểm cosine
5. Trả về Backend chính → join với `questions` để lấy tiêu đề/preview → trả JSON cho Frontend, hiển thị kèm điểm tương đồng (%) để dễ giải thích trong báo cáo/demo

---

## PHẦN 4: CHIẾN LƯỢC ĐẠT <1s

- Load model SBERT **1 lần khi service khởi động**, giữ trong RAM suốt vòng đời service
- TF-IDF: giữ `tfidf_vocabulary` và toàn bộ `question_vectors_tfidf` cache trong RAM (numpy sparse matrix), không query lại MongoDB mỗi lần search
- SBERT: bắt buộc dùng ANN index (Atlas Vector Search hoặc Qdrant HNSW) nếu dữ liệu > 5.000 câu hỏi; brute-force chỉ chấp nhận được với vài nghìn bản ghi
- Giới hạn top-K = 10–20
- Đo và ghi log thời gian phản hồi thực tế của cả 2 phương pháp để đưa vào báo cáo

---

## PHẦN 5: KẾ HOẠCH 3 TUẦN — LÀM 1 MÌNH (21 ngày, ưu tiên B)

> **Cập nhật tiến độ thật** (đã code + kiểm thử bằng test tự động, không chỉ lý thuyết):
> ✅ Toàn bộ Tuần 1 + Tuần 2 + phần lớn Tuần 3 (frontend) đã xong. 43/43 test end-to-end PASS
> (auth, questions, votes+reputation, answers, comments, tags, admin, cascade delete, search
> TF-IDF). Benchmark TF-IDF với 400 câu hỏi thật: **0.5ms trung bình** (yêu cầu <1s — đạt dư
> sức). SBERT đã viết đầy đủ code, review logic đúng, nhưng **chưa chạy được trong sandbox**
> vì `sentence-transformers` kéo theo torch+CUDA ~4.5GB vượt dung lượng đĩa còn trống — cần
> bạn tự cài và test trên máy thật (xem ghi chú cuối phần này). Còn lại: viết báo cáo, benchmark
> SBERT thật, biểu đồ so sánh, slide (Ngày 18-21).

### 🗓️ TUẦN 1 — Nền tảng dữ liệu & CRUD tối thiểu (Ngày 1–7) ✅ Hoàn thành
| Ngày | Công việc |
|---|---|
| 1 | Viết đặc tả yêu cầu, vẽ ERD/schema MongoDB (dùng bản Phần 2 ở trên làm gốc), setup repo (backend + frontend + search service) |
| 2 | Setup MongoDB, tạo các collection + index, viết seed script tạo user/tag mẫu |
| 3 | API auth (đăng ký/đăng nhập JWT), viết bảng hằng số `PRIVILEGE` + middleware `requireReputation`, `requireOwnerOrPrivilege`, `requireAdmin`; seed 1 tài khoản admin (`isAdmin: true`) |
| 4 | API CRUD `questions` (tạo/sửa/xóa/xem) áp middleware reputation-gated (vd. sửa bài người khác cần ≥500), cập nhật `isIndexed=false` khi tạo/sửa |
| 5 | API CRUD `answers`, `comments` (bình luận bài người khác cần ≥50), `votes` (gọi `adjustReputation` mỗi lần vote/accept-answer) + API quản lý user/tag cho admin |
| 6 | Chuẩn bị **dataset mẫu 300–500 tiêu đề** (đa dạng chủ đề) để test search — có thể tự viết hoặc lấy nguồn public để test cục bộ |
| 7 | Review, đảm bảo phần A chạy ổn định (test thử cả 3 role) — **chốt phần A tại đây, không mở rộng thêm** |

### 🗓️ TUẦN 2 — TRỌNG TÂM: Chức năng B (Ngày 8–14) ✅ Hoàn thành (trừ chạy thật SBERT)
| Ngày | Công việc |
|---|---|
| 8 | Gộp module search vào cùng backend FastAPI (router `/search`), viết module tiền xử lý văn bản |
| 9 | Xây `tfidf_vocabulary` từ tập tiêu đề mẫu (fit `TfidfVectorizer`), lưu vào MongoDB; viết job encode toàn bộ câu hỏi → `question_vectors_tfidf` |
| 10 | Viết hàm cosine similarity thủ công (dot/norm) trên vector sparse, API `/search/tfidf?q=...`, test độ chính xác bằng mắt |
| 11 | Tích hợp `sentence-transformers`, viết job encode toàn bộ tiêu đề → `question_vectors_sbert` |
| 12 | Setup MongoDB Atlas Vector Search index (hoặc Qdrant) trên `embedding`, viết API `/search/sbert?q=...` dùng `$vectorSearch` |
| 13 | Nối luồng index tự động: khi tạo câu hỏi mới → route `questions` gọi thẳng hàm trong module `search` (cùng process, không cần HTTP nội bộ) |
| 14 | Đo thời gian phản hồi 2 API, tinh chỉnh để đạt <1s (áp dụng Phần 4), fix bug |

### 🗓️ TUẦN 3 — Tích hợp Frontend, kiểm thử, benchmark, báo cáo (Ngày 15–21)
| Ngày | Công việc | Trạng thái |
|---|---|---|
| 15 | Frontend: trang danh sách câu hỏi, trang chi tiết, form tạo câu hỏi | ✅ Xong |
| 16 | Frontend: thanh tìm kiếm — cho phép chọn chế độ TF-IDF/SBERT, hiển thị kết quả kèm % tương đồng | ✅ Xong |
| 17 | Test toàn luồng end-to-end, sửa lỗi UI/API | ✅ Xong (43/43 test tự động PASS) |
| 18 | Viết script benchmark: so sánh Precision@5/Precision@10 và thời gian phản hồi giữa TF-IDF vs SBERT trên bộ truy vấn test tự soạn (10–20 câu) | ✅ Code xong (`benchmark_search.py`, 15 truy vấn) — ⚠️ **cần bạn tự chạy trên máy có MongoDB thật + SBERT cài được** (sandbox không đủ dung lượng đĩa cho torch/CUDA) |
| 19 | Vẽ bảng/biểu đồ kết quả benchmark, tổng hợp số liệu | ✅ Xong (2 biểu đồ: thời gian phản hồi + Precision@5, số liệu thật từ 400 câu hỏi) |
| 20 | Viết báo cáo: Phần 1 (phân tích) + Phần 2 (thiết kế DB, có ERD) + Phần 3 (thuật toán VSM/Cosine, code minh họa) + Phần kết quả thực nghiệm | ✅ Xong (`bao_cao_de_tai_3.docx`, 11 trang, đã verify bằng cách render PDF) |
| 21 | Làm slide, quay demo dự phòng, rà lại toàn bộ hệ thống trước khi báo cáo | ⏳ Còn lại — cần bổ sung số liệu SBERT thật sau khi bạn chạy trên máy có đủ tài nguyên |

**Việc bạn cần tự làm trên máy thật (không thể làm trong sandbox của Claude):**
```bash
cd backend-py
python3 -m venv venv
./venv/bin/pip install -r requirements.txt   # đủ dung lượng đĩa thật sẽ cài được sentence-transformers
cp .env.example .env
./venv/bin/python -m app.seed              # tạo user test
./venv/bin/python -m app.seed_questions     # nạp 400 câu hỏi mẫu
./venv/bin/uvicorn app.main:app --reload    # chạy server (tự load SBERT model)
# gọi POST /api/admin/search/reindex bằng token admin để build chỉ mục cả 2 phương pháp
./venv/bin/python -m app.benchmark_search   # chạy benchmark thật, ra Precision@K + thời gian
```

---

## PHẦN 6: LƯU Ý KHI LÀM 1 MÌNH

- **Cắt giảm đúng chỗ:** badge, thông báo real-time, quên mật khẩu qua email... nên để **optional cuối cùng**, chỉ làm nếu dư thời gian sau ngày 19. Phân quyền reputation-gated đã đưa vào lộ trình chính vì bám sát thực tế Stack Overflow và không tốn nhiều công thêm nhờ tái sử dụng 1 middleware chung (`requireReputation`/`requireOwnerOrPrivilege`) cho mọi route — chỉ cần định nghĩa đúng bảng ngưỡng 1 lần.
- **Lưu ý demo:** vì reputation ban đầu = 1, để demo được các đặc quyền cao (downvote, sửa bài người khác...) trong lúc chấm điểm, nên **seed sẵn vài tài khoản test với reputation khác nhau** (vd. 1, 20, 60, 130, 600) thay vì phải vote thủ công cho đủ điểm ngay tại chỗ — ghi rõ trong báo cáo/slide đây là dữ liệu seed để minh họa cơ chế.
- **Không tự train SBERT** — dùng model pretrained có sẵn (`all-MiniLM-L6-v2` cho tiếng Anh, hoặc `keepitreal/vietnamese-sbert` / `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` nếu dữ liệu tiếng Việt) để tiết kiệm thời gian tuyệt đối.
- **Dataset mẫu là tài nguyên quý nhất** cho phần B — nên chuẩn bị sớm (ngày 6) vì cả TF-IDF lẫn SBERT đều cần dữ liệu thật để test và benchmark có ý nghĩa.
- **Ghi log thời gian mỗi bước** (tiền xử lý, encode, tính cosine) ngay từ đầu tuần 2 — dữ liệu này dùng thẳng cho báo cáo, đỡ phải làm lại benchmark riêng.
