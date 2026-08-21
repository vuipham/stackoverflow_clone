# Hướng dẫn chạy benchmark SBERT thật (trên máy của bạn)

Claude không chạy được phần này trong sandbox vì `sentence-transformers` kéo theo
`torch` bản mặc định (~4.5GB, bao gồm thư viện CUDA dù không có GPU) — vượt quá
dung lượng đĩa còn trống trong môi trường sandbox. Trên máy cá nhân, làm theo các
bước dưới đây, có thể tránh vấn đề này bằng cách cài `torch` bản CPU-only trước.

## Các bước

```bash
cd backend
python3 -m venv venv

# Kích hoạt venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# QUAN TRỌNG: cài torch bản CPU-only TRƯỚC để tránh tải nhầm bản CUDA nặng ~4GB
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Cài phần còn lại (torch đã có sẵn, sẽ không tải lại)
pip install -r requirements.txt

# Chạy MongoDB thật (Docker) - hoặc dùng MongoDB đã cài sẵn trên máy
docker run -d -p 27017:27017 --name mongo mongo:7

cp .env.example .env

# Tạo dữ liệu: user test + 400 câu hỏi mẫu
python -m app.seed
python -m app.seed_questions

# Chạy server (lần đầu sẽ tự tải model SBERT ~470MB từ HuggingFace, cần mạng)
uvicorn app.main:app --reload
```

Mở **http://localhost:8000/docs** (Swagger UI), đăng nhập bằng tài khoản `admin`
(mật khẩu `Test@123`) qua `/api/auth/login`, copy token, bấm nút **Authorize** ở
góc trên bên phải Swagger UI để dán token vào, sau đó gọi:

```
POST /api/admin/search/reindex
```

để xây chỉ mục cho cả TF-IDF lẫn SBERT.

Cuối cùng, mở **terminal mới** (activate lại venv), chạy:

```bash
python -m app.benchmark_search
```

Script sẽ tự động chạy 15 truy vấn test cho cả 2 phương pháp, in ra bảng so sánh
Precision@5/@10 và thời gian phản hồi, đồng thời ghi log vào MongoDB.

## Sau khi có kết quả

Gửi lại output (hoặc chụp màn hình bảng kết quả) cho Claude — mình sẽ cập nhật
số liệu thật vào mục 4.3 của báo cáo (`bao_cao_de_tai_3.docx`), thay cho phần dự
đoán hiện tại, và có thể vẽ thêm biểu đồ so sánh trực tiếp TF-IDF vs SBERT.

## Nếu gặp lỗi thường gặp
- **`No space left on device`**: kiểm tra dung lượng đĩa trống (`df -h`), torch
  CPU-only cần khoảng 1-2GB, model SBERT tải về thêm ~470MB.
- **Server không tải được model SBERT (lỗi mạng)**: `/api/search/sbert` sẽ trả lỗi
  503 nhưng server vẫn chạy bình thường — kiểm tra kết nối mạng tới huggingface.co.
- **`docker: command not found`**: cài Docker Desktop, hoặc cài MongoDB trực tiếp
  theo hướng dẫn tại mongodb.com/docs/manual/installation.
