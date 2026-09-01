# BỘ GIÁO DỤC VÀ ĐÀO TẠO
# ĐẠI HỌC CẦN THƠ
# TRƯỜNG CÔNG NGHỆ THÔNG TIN & TRUYỀN THÔNG

---

# BÁO CÁO ĐỒ ÁN / NIÊN LUẬN
## NGÀNH CÔNG NGHỆ THÔNG TIN

### Đề tài
# HỆ THỐNG QUẢN TRỊ TRI THỨC
### (Stack Overflow Clone tích hợp Tìm kiếm ngữ nghĩa TF-IDF)

**KNOWLEDGE MANAGEMENT SYSTEM**

Sinh viên: [Họ và tên sinh viên]
Mã số: [.....................]
Khóa: [K..]

Cần Thơ, 2026

---

# BỘ GIÁO DỤC VÀ ĐÀO TẠO
# ĐẠI HỌC CẦN THƠ
# TRƯỜNG CÔNG NGHỆ THÔNG TIN & TRUYỀN THÔNG
# KHOA CÔNG NGHỆ THÔNG TIN

---

# BÁO CÁO ĐỒ ÁN / NIÊN LUẬN
## NGÀNH CÔNG NGHỆ THÔNG TIN

### Đề tài
# HỆ THỐNG QUẢN TRỊ TRI THỨC
### (Stack Overflow Clone tích hợp Tìm kiếm ngữ nghĩa TF-IDF)

**KNOWLEDGE MANAGEMENT SYSTEM**

Người hướng dẫn: [ThS/TS. .................]
Sinh viên thực hiện: [Họ và tên sinh viên]
MSSV: [.....................]
Khóa: [K..]

Cần Thơ, 2026

---

# LỜI CẢM ƠN

Em xin chân thành cảm ơn Quý Thầy/Cô Trường Công nghệ Thông tin & Truyền thông, Đại học Cần Thơ đã tận tình giảng dạy và truyền đạt kiến thức trong suốt quá trình học tập. Đặc biệt, em xin gửi lời cảm ơn sâu sắc đến Thầy/Cô [.................] — người đã trực tiếp hướng dẫn, góp ý và hỗ trợ em trong suốt quá trình thực hiện đề tài này.

Do thời gian và kiến thức còn hạn chế, báo cáo khó tránh khỏi thiếu sót. Em rất mong nhận được sự góp ý của Quý Thầy/Cô để đề tài được hoàn thiện hơn.

Em xin chân thành cảm ơn!

Cần Thơ, ngày ..... tháng ..... năm 2026

Sinh viên thực hiện

---

# MỤC LỤC

- LỜI CẢM ƠN
- DANH MỤC HÌNH ẢNH
- DANH MỤC BẢNG
- TÓM LƯỢC
- PHẦN GIỚI THIỆU
- CHƯƠNG 1: ĐẶC TẢ YÊU CẦU
- CHƯƠNG 2: THIẾT KẾ GIẢI PHÁP
- CHƯƠNG 3: CÀI ĐẶT GIẢI PHÁP
- CHƯƠNG 4: ĐÁNH GIÁ KIỂM THỬ
- PHẦN KẾT LUẬN
- TÀI LIỆU THAM KHẢO
- PHỤ LỤC

---

# DANH MỤC HÌNH ẢNH

- Hình 1.1 — Sơ đồ Use Case của hệ thống
- Hình 2.1 — Sơ đồ quan hệ (ERD) giữa các collection MongoDB
- Hình 4.1 — Thời gian phản hồi TF-IDF trên 15 truy vấn test
- Hình 4.2 — Precision@5 của TF-IDF trên từng truy vấn test

---

# DANH MỤC BẢNG

- Bảng 2.1 — Công nghệ sử dụng trong hệ thống
- Bảng 4.1 — Kết quả thực nghiệm TF-IDF

---

# TÓM LƯỢC

## Tiếng Việt

Trong một tổ chức, kiến thức và kinh nghiệm kỹ thuật thường bị phân tán, khiến cùng một vấn đề có thể bị hỏi đi hỏi lại nhiều lần. Đề tài xây dựng Hệ thống Quản trị tri thức theo mô hình Stack Overflow, cho phép thành viên trong tổ chức đặt câu hỏi, trả lời, bình luận, bỏ phiếu và gắn thẻ chủ đề, với cơ chế phân quyền theo điểm uy tín (reputation) bám sát mô hình thực tế thay vì vai trò cố định. Chức năng đặc thù của đề tài là tìm kiếm bài thảo luận theo tiêu đề dựa trên mức độ tương đồng ngữ nghĩa, được cài đặt bằng mô hình không gian vector với trọng số TF-IDF. Vector chỉ mục được lưu trữ trong MongoDB, và độ tương đồng giữa truy vấn với tiêu đề được đo bằng độ đo Cosine Similarity. Hệ thống được thực nghiệm trên bộ dữ liệu thật gồm 5.969 câu hỏi với 15 truy vấn kiểm thử, đo thời gian phản hồi và Precision@K. Kết quả cho thấy phương pháp TF-IDF đạt yêu cầu thời gian phản hồi dưới 1 giây với biên độ rất lớn (trung bình 11,98ms), và đạt Precision@5 trung bình 0,65 trên bộ truy vấn thử nghiệm.

## English

Within an organization, technical knowledge and experience are often scattered, causing the same problem to be asked repeatedly. This project builds a Knowledge Management System modeled after Stack Overflow, allowing members to ask questions, answer, comment, vote, and tag topics, with a reputation-gated permission system that mirrors real-world community platforms rather than static roles. The project's core feature is searching discussion threads by title based on semantic similarity, implemented through a Vector Space Model with TF-IDF weighting. The index vectors are stored in MongoDB, and similarity between a query and titles is measured with Cosine Similarity. The system was evaluated on a real dataset of 5,969 questions with 15 test queries, measuring response time and Precision@K. Results show the TF-IDF method comfortably meets the sub-1-second response requirement (averaging 11.98ms), and achieves an average Precision@5 of 0.65 on the test set.

---

# PHẦN GIỚI THIỆU

## Đặt vấn đề

Trong một tổ chức — có thể là một công ty công nghệ, một trường học hay một cộng đồng lập trình viên — kiến thức và kinh nghiệm thường bị phân tán ở nhiều nơi khác nhau: người này biết cách xử lý một lỗi kỹ thuật nhưng không ai khác biết, người khác đã từng gặp một vấn đề tương tự nhưng không có nơi nào để ghi lại. Hệ quả là cùng một câu hỏi có thể bị hỏi đi hỏi lại nhiều lần, gây mất thời gian và làm chậm công việc chung.

Khi số lượng câu hỏi trong hệ thống ngày càng lớn, việc tìm kiếm theo cách so khớp chuỗi ký tự đơn thuần (LIKE/regex) sẽ không hiệu quả: không tìm ra được các câu hỏi có nội dung liên quan nhưng dùng từ ngữ khác, và không sắp xếp được kết quả theo mức độ liên quan thật sự. Đây là lý do đề tài cần xây dựng một cơ chế tìm kiếm thông minh dựa trên mức độ tương đồng ngữ nghĩa giữa từ khóa và tiêu đề câu hỏi.

## Mục tiêu đề tài

- Xây dựng hệ thống hỏi–đáp tri thức kiểu Stack Overflow: đăng câu hỏi, trả lời, bình luận, vote, gắn thẻ (tag) chủ đề.
- Xây dựng module tìm kiếm bài thảo luận theo tiêu đề bằng từ khóa, dựa trên Vector Space Model (TF-IDF).
- Lưu trữ các vector chỉ mục vào MongoDB và đo độ tương đồng bằng Cosine Similarity.
- Đo lường, đánh giá định lượng phương pháp bằng thời gian phản hồi và độ chính xác Precision@K.

## Đối tượng và phạm vi nghiên cứu

- **Đối tượng:** thành viên trong một tổ chức cần tra cứu và chia sẻ tri thức kỹ thuật với nhau.
- **Phạm vi chức năng:** 3 nhóm tác nhân — Khách (chưa đăng nhập), Thành viên (quyền mở dần theo điểm uy tín — reputation), Quản trị viên (tài khoản cố định, không qua reputation).
- **Phạm vi kỹ thuật:** tập trung vào chức năng tìm kiếm ngữ nghĩa theo tiêu đề bằng mô hình không gian vector TF-IDF.

## Phương pháp nghiên cứu

- Phân tích yêu cầu bằng sơ đồ Use Case; thiết kế dữ liệu bằng sơ đồ quan hệ thực thể (ERD) phù hợp với MongoDB (document-based).
- Nghiên cứu và cài đặt phương pháp vector hoá văn bản TF-IDF (mô hình không gian vector cổ điển).
- Thực nghiệm định lượng: xây dựng bộ 15 truy vấn kiểm thử trên bộ dữ liệu thật gồm 5.969 câu hỏi, đo mỗi truy vấn 5 lần và lấy trung bình để đảm bảo số liệu ổn định.

## Nội dung nghiên cứu

Đề tài do một sinh viên thực hiện độc lập, bao gồm toàn bộ các công việc: phân tích yêu cầu, thiết kế cơ sở dữ liệu, cài đặt backend (FastAPI + MongoDB) và frontend (SvelteKit), cài đặt module tìm kiếm ngữ nghĩa (TF-IDF), xây dựng kịch bản benchmark, thực nghiệm và viết báo cáo.

## Bố cục của quyển báo cáo

Ngoài Phần giới thiệu, báo cáo gồm 4 chương nội dung: Chương 1 trình bày đặc tả yêu cầu của hệ thống; Chương 2 trình bày thiết kế giải pháp (kiến trúc, cơ sở dữ liệu, giải thuật); Chương 3 trình bày cách cài đặt giải pháp; Chương 4 trình bày kết quả đánh giá, kiểm thử. Phần kết luận tổng kết kết quả đạt được và hướng phát triển.

---

# CHƯƠNG 1: ĐẶC TẢ YÊU CẦU

## 1.1. Mô tả tổng quan hệ thống

Hệ thống Quản trị tri thức hoạt động theo mô hình tương tự trang Stack Overflow: là nơi mọi thành viên trong tổ chức có thể đặt câu hỏi, chia sẻ câu trả lời, thảo luận và tra cứu lại các kiến thức đã có sẵn một cách nhanh chóng thông qua chức năng tìm kiếm thông minh theo tiêu đề. Một điểm khác biệt quan trọng so với mô hình phân quyền tĩnh (chỉ có "thành viên thường" và "quản trị viên") là hệ thống áp dụng đúng cơ chế thật của Stack Overflow: quyền hạn của một thành viên tăng dần theo điểm uy tín (reputation) mà họ tích lũy được từ những đóng góp có ích, chứ không được cấp cố định.

**Quy trình làm việc điển hình của một thành viên:** khi gặp vấn đề, họ tìm kiếm xem đã có ai hỏi vấn đề tương tự chưa; nếu có, họ đọc câu trả lời, bình luận hoặc bỏ phiếu; nếu chưa, họ đặt câu hỏi mới và gắn thẻ liên quan. Nhờ điểm uy tín tích lũy dần từ việc trả lời hữu ích, họ dần được mở thêm quyền: bình luận vào bài người khác, downvote, sửa bài người khác khi phát hiện sai sót, và ở mức cao nhất là xóa câu hỏi vi phạm của người khác. Quản trị viên là tài khoản đặc biệt không mở quyền qua điểm uy tín mà được cấp cố định, phụ trách quản lý tài khoản, quản lý thẻ hệ thống và theo dõi "sức khỏe" của module tìm kiếm.

## 1.2. Yêu cầu chức năng — Sơ đồ Use Case

Sơ đồ dưới đây thể hiện các trường hợp sử dụng (use case) chính của hệ thống, ứng với 3 tác nhân: Khách (chưa đăng nhập), Thành viên (quyền mở dần theo điểm uy tín) và Quản trị viên (tài khoản cố định, không qua reputation). Hệ thống không có vai trò "Điều hành viên (Moderator)" tách riêng — các quyền kiểm duyệt (sửa/xóa bài người khác) được gộp vào chính cơ chế reputation của Thành viên.

**Hình 1.1 — Sơ đồ Use Case của hệ thống**

### Mô tả một số use case chính

- **Tìm kiếm theo tiêu đề (TF-IDF)** — actor: Khách, Thành viên. Người dùng nhập từ khóa; hệ thống vector hóa từ khóa, tính độ tương đồng cosine với vector đã lập chỉ mục cho từng tiêu đề, trả về danh sách sắp xếp theo độ liên quan giảm dần. Đây là use case mở rộng (extend) của "Xem danh sách câu hỏi".
- **Đặt câu hỏi** — actor: Thành viên (rep ≥ 1). Bao gồm (include) use case "Gắn thẻ (tag) cho câu hỏi", vì mỗi câu hỏi tạo mới đều đi kèm bước gắn tag.
- **Sửa bài người khác / Xóa câu hỏi người khác** — hai use case mở rộng (extend) tương ứng của "Sửa bài viết của chính mình" và "Downvote", chỉ khả dụng khi điểm uy tín của thành viên đạt ngưỡng 500 và 2000.
- **Quản lý người dùng / Quản lý tag / Xây lại chỉ mục / Xem log benchmark** — bốn use case chỉ dành riêng cho Quản trị viên, không phụ thuộc điểm uy tín.

## 1.3. Yêu cầu phi chức năng

- Thời gian phản hồi tìm kiếm phải nhỏ hơn 1 giây.
- Hệ thống phải tự động cập nhật lại chỉ mục (re-index) khi có câu hỏi mới/sửa/xóa.
- Giao diện tối giản, đủ để trình diễn luồng nghiệp vụ chính: tạo câu hỏi → tìm kiếm → xem kết quả xếp hạng theo độ tương đồng.

---

# CHƯƠNG 2: THIẾT KẾ GIẢI PHÁP

## 2.1. Kiến trúc tổng thể & công nghệ sử dụng

Backend và module xử lý vector dùng chung một service Python (FastAPI) — không tách microservice riêng — nhờ đó khỏi cần thêm một tầng gọi HTTP nội bộ, dễ triển khai và bảo trì hơn với quy mô một sinh viên thực hiện.

| Thành phần | Lựa chọn |
|---|---|
| Backend | Python (FastAPI) — API chính + module search dùng chung 1 service |
| Driver MongoDB | Motor (async) |
| Xác thực | PyJWT + bcrypt (hash password) |
| Xử lý vector | scikit-learn (TfidfVectorizer) |
| Frontend | Svelte (SvelteKit, chế độ SPA) |

**Bảng 2.1 — Công nghệ sử dụng trong hệ thống**

## 2.2. Thiết kế cơ sở dữ liệu (ERD)

Vì dữ liệu bài thảo luận có cấu trúc linh hoạt và cần lưu trữ thêm vector số thực nhiều chiều (TF-IDF) đi kèm mỗi tiêu đề, mô hình dữ liệu dạng tài liệu (document-based) như MongoDB phù hợp hơn quan hệ (SQL) truyền thống. Collection lưu vector chỉ mục được tách riêng khỏi collection questions chính để: (a) dễ re-index độc lập, (b) không làm phình document chính, (c) dễ chuyển sang Vector Database riêng sau này mà không đụng schema chính.

**Hình 2.1 — Sơ đồ quan hệ (ERD) giữa các collection MongoDB**

### Mô tả các collection chính

| Collection | Vai trò |
|---|---|
| users | Tài khoản, reputation, reputationLog, cờ isAdmin/isBanned |
| questions | Câu hỏi — trường title là dữ liệu nguồn cho vector hóa (chức năng B) |
| answers / comments / votes / tags | Nghiệp vụ nền tảng chuẩn kiểu Stack Overflow |
| tfidf_vocabulary | Vocab + IDF toàn cục — bắt buộc để encode câu truy vấn đúng không gian với vector đã lưu |
| question_vectors_tfidf | Vector TF-IDF dạng sparse (term_index → weight) + norm, theo từng vocabVersion |
| search_benchmark_log | Log thời gian phản hồi mỗi lượt search — dùng cho phần thực nghiệm |

## 2.3. Phân quyền theo Reputation (Reputation-Gated Privileges)

Thay vì dùng RBAC tĩnh (User/Moderator/Admin), hệ thống mô phỏng đúng cơ chế thật của Stack Overflow: quyền hạn mở dần theo điểm uy tín (reputation) tích lũy được.

| Reputation | Đặc quyền mở ra |
|---|---|
| 1 (mặc định) | Đặt câu hỏi, trả lời câu hỏi |
| 15 | Upvote |
| 50 | Bình luận vào bài của người khác |
| 125 | Downvote |
| 500 | Sửa bài viết của người khác trực tiếp |
| 2000 | Xóa / khôi phục câu hỏi của người khác |

| Sự kiện | Thay đổi reputation |
|---|---|
| Bài viết được upvote | +10 |
| Câu trả lời được chấp nhận (accepted) | +15 |
| Bài viết bị downvote | −2 |
| Chủ động downvote người khác | −1 (chi phí downvote) |

Admin là cờ isAdmin riêng biệt, tách hoàn toàn khỏi cơ chế reputation (giống thực tế: admin là nhân viên vận hành, không phải mở bằng điểm).

## 2.4. Thiết kế giải thuật tìm kiếm ngữ nghĩa

Chức năng đặc thù của đề tài — tìm kiếm bài thảo luận theo tiêu đề — được thiết kế theo luồng xử lý tổng quát: Index (khi tạo/sửa câu hỏi) và Search (khi người dùng tìm kiếm).

### Phương pháp — TF-IDF (Vector Space Model cổ điển)

- **Tiền xử lý tiêu đề:** chuyển chữ thường, tách từ, bỏ stop-word.
- **Trọng số TF-IDF:** trọng số mỗi từ trong vector = TF (tần suất từ trong tiêu đề đó) × IDF (nghịch đảo tần suất văn bản — từ càng hiếm gặp ở các tiêu đề khác thì trọng số càng cao).
- **Vector được lưu dạng thưa (sparse)** — chỉ lưu từ có trọng số khác 0 để tiết kiệm bộ nhớ và tăng tốc tính cosine trên tập dữ liệu lớn.

### Công thức Cosine Similarity

Độ tương đồng giữa vector truy vấn A và vector tiêu đề B được tính bằng:

```
cosine(A, B) = (A · B) / (‖A‖ × ‖B‖)
```

Giá trị càng gần 1 nghĩa là từ khóa và tiêu đề càng giống nhau; càng gần 0 nghĩa là không liên quan. Kết quả được sắp xếp theo độ tương đồng giảm dần, trả về top-K bài thảo luận liên quan nhất.

---

# CHƯƠNG 3: CÀI ĐẶT GIẢI PHÁP

## 3.1. Môi trường và công nghệ cài đặt

- **Ngôn ngữ:** Python 3.11 (backend + xử lý vector), TypeScript/Svelte (frontend).
- **Thư viện chính:** scikit-learn (TfidfVectorizer), FastAPI, Motor (MongoDB driver bất đồng bộ), PyJWT, bcrypt.
- **Cơ sở dữ liệu:** MongoDB, chạy độc lập, không cần Vector Database chuyên dụng ở quy mô hiện tại.

## 3.2. Cài đặt luồng Index

1. Câu hỏi được lưu vào collection questions với cờ isIndexed = false khi vừa tạo.
2. Tiêu đề được tiền xử lý (lowercase, tách từ, bỏ stop-word).
3. Sinh vector TF-IDF (dựa trên vocabulary hiện hành).
4. Lưu vào collection question_vectors_tfidf, cập nhật isIndexed = true.
5. Toàn bộ vocabulary/vector TF-IDF được load 1 lần lúc khởi động server, giữ trong RAM suốt vòng đời service — không truy vấn lại MongoDB ở mỗi lượt tìm kiếm.

## 3.3. Cài đặt luồng Search

Hàm tính Cosine Similarity cho vector TF-IDF dạng thưa (sparse) — tự tính norm riêng cho từng vector thay vì để scikit-learn tự L2-normalize sẵn (đúng công thức cosine = dot(a,b) / (norm_a × norm_b)):

```python
def cosine(vec_a, norm_a, vec_b, norm_b):
    if norm_a == 0 or norm_b == 0:
        return 0.0
    # Dot product qua giao 2 dict thưa (sparse)
    small, big = (vec_a, vec_b) if len(vec_a) < len(vec_b) else (vec_b, vec_a)
    dot = sum(w * big[idx] for idx, w in small.items() if idx in big)
    return dot / (norm_a * norm_b)
```

Luồng tìm kiếm: (1) tiền xử lý câu truy vấn giống hệt bước index, (2) vector hoá bằng đúng vocabulary đã dùng lúc index, (3) tính cosine với toàn bộ vector đã cache trong RAM, (4) trả về top-K kèm điểm tương đồng (%) để hiển thị trên giao diện.

Toàn bộ code cài đặt đầy đủ (bao gồm luồng reindex, API endpoint, và script benchmark) nằm tại `backend/app/routers/search.py` và `backend/app/benchmark_search.py` trong mã nguồn đề tài.

---

# CHƯƠNG 4: ĐÁNH GIÁ KIỂM THỬ

## 4.1. Mục tiêu và môi trường kiểm thử

- **Mục tiêu:** kiểm chứng yêu cầu phi chức năng (thời gian phản hồi < 1 giây) và đánh giá độ chính xác của phương pháp tìm kiếm.
- **Dataset:** 5.969 câu hỏi thật trong hệ thống, đa chủ đề (mongodb, react, docker, jwt, machine-learning, nlp, python, kubernetes, fastapi, qdrant, cosine-similarity, github-actions, django, redis, rest-api...).
- **Bộ truy vấn test:** 15 câu hỏi tự soạn, mỗi câu gắn với 1 tag "đúng" để tính Precision@K (một kết quả được coi là relevant nếu tag đó nằm trong tags của câu hỏi trả về).
- **Mỗi truy vấn được đo 5 lần**, lấy trung bình để số liệu ổn định.
- **Reindex TF-IDF** (fit vocabulary cho toàn bộ 5.969 câu hỏi): 346,8ms, không gian từ vựng 311 chiều.

## 4.2. Kết quả TF-IDF

| Chỉ số | Giá trị |
|---|---|
| Thời gian phản hồi trung bình | 11,98 ms |
| Thời gian phản hồi cao nhất | 13,57 ms |
| Thời gian phản hồi thấp nhất | 7,99 ms |
| Precision@5 trung bình | 0,65 |
| Precision@10 trung bình | 0,64 |
| Đạt yêu cầu < 1000ms? | ĐẠT (nhanh hơn yêu cầu ~74–125 lần) |

**Bảng 4.1 — Kết quả thực nghiệm TF-IDF**

**Hình 4.1 — Thời gian phản hồi TF-IDF trên 15 truy vấn test**

**Hình 4.2 — Precision@5 của TF-IDF trên từng truy vấn test**

### Nhận xét

- **Về tốc độ:** TF-IDF vượt xa yêu cầu <1s (trung bình chưa tới 12ms) nhờ chiến lược cache toàn bộ vocabulary và vector trong RAM — không có truy vấn MongoDB nào trong đường đi search.
- **Về độ chính xác:** một số truy vấn đạt tuyệt đối (1,0) khi từ khóa trùng khớp trực tiếp với tiêu đề (vd. "xác thực người dùng bằng JWT", "xây dựng REST API chuẩn"), nhưng một số đạt 0,0 khi câu hỏi diễn đạt cùng ý nhưng dùng từ vựng khác (vd. "triển khai mô hình học máy" không khớp từ với các tiêu đề dùng thuật ngữ khác cho machine-learning). Đây chính là hạn chế cố hữu của TF-IDF: chỉ khớp được khi có sự trùng lặp từ vựng (lexical matching), không hiểu được ngữ nghĩa/từ đồng nghĩa.

---

# PHẦN KẾT LUẬN

## Kết quả đạt được

- Đã cài đặt đầy đủ chức năng nền tảng kiểu Stack Overflow với cơ chế phân quyền theo reputation bám sát thực tế.
- Chức năng đặc thù — tìm kiếm ngữ nghĩa — đã hoàn chỉnh phương pháp TF-IDF, kiểm thử thật trên 5.969 câu hỏi với kết quả cụ thể, minh bạch (không chỉ dự kiến lý thuyết).
- Phương pháp TF-IDF đạt yêu cầu thời gian phản hồi dưới 1 giây với biên độ rất lớn.
- Đã phân tích được điểm mạnh/yếu thực nghiệm của phương pháp thay vì chỉ dựa trên giả thuyết lý thuyết.

## Hướng phát triển

- Nghiên cứu bổ sung phương pháp Sentence-BERT (SBERT) để so sánh và kết hợp (hybrid search: re-rank top-K) nhằm cải thiện độ chính xác ở các truy vấn dùng từ đồng nghĩa.
- Khi dữ liệu vượt ngưỡng lớn (>5.000–10.000 câu hỏi): chuyển sang Vector Database chuyên dụng (MongoDB Atlas Vector Search hoặc Qdrant) thay cho brute-force cosine.
- Mở rộng bộ truy vấn kiểm thử (hiện 15 câu) để đánh giá chắc chắn hơn về mặt thống kê.
- Bổ sung các chức năng phụ nếu còn thời gian: hệ thống huy hiệu (badge), thông báo real-time.

---

# TÀI LIỆU THAM KHẢO

[1] Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press.

[2] scikit-learn developers. *TfidfVectorizer documentation*. https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html

[3] MongoDB Inc. *MongoDB Manual*. https://www.mongodb.com/docs/

[4] Stack Overflow. *Stack Exchange reputation privileges*. https://stackoverflow.com/help/privileges

[5] FastAPI documentation. https://fastapi.tiangolo.com/

---

# PHỤ LỤC — HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG

## A. Cài đặt backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## B. Chạy benchmark tìm kiếm

```bash
cd backend
python -m app.benchmark_search
```

Script sẽ tự động reindex TF-IDF, chạy 15 truy vấn test, đo Precision@5/@10 và thời gian phản hồi, rồi ghi log vào collection `search_benchmark_log` để phục vụ báo cáo.

## C. Cài đặt frontend

```bash
cd frontend
npm install
npm run dev