# Frontend Svelte — Hệ thống quản trị tri thức (Đề tài 3)

SvelteKit (Svelte 5, runes mode) + TypeScript. Chế độ SPA (adapter-static, fallback
index.html) vì toàn bộ dữ liệu fetch phía client từ backend FastAPI, không dùng SSR.

## ✅ Đã kiểm thử thật (không chỉ svelte-check suông)
- `npm run check` (svelte-check + TypeScript) → **0 lỗi, 0 cảnh báo**
- `npm run build` → build production thành công
- Đã dựng **backend thật (FastAPI + mongomock, seed 400 câu hỏi + reindex TF-IDF)** và
  **frontend dev server thật** chạy song song trong sandbox, sau đó:
  - curl toàn bộ 7 route (`/`, `/questions`, `/search`, `/login`, `/register`, `/ask`,
    `/admin`) → tất cả trả HTTP 200, đúng nội dung mong đợi (đã grep các chuỗi UI như
    "TF-IDF", "SBERT", "Trang quản trị" trong HTML trả về)
  - Gọi thẳng chuỗi API mà UI mới gọi (login → tạo câu hỏi → tạo answer → accept answer →
    tạo comment → search TF-IDF) bằng curl để xác nhận **shape JSON khớp chính xác** với
    các TypeScript interface trong `src/lib/api/client.ts` (không lệch field name)

## Yêu cầu
- Node.js >= 18
- Backend đang chạy tại `http://localhost:8000` (xem `../backend-py/README.md`) — **đã
  chạy `seed.py` + `seed_questions.py` + gọi `POST /api/admin/search/reindex` ít nhất 1
  lần**, nếu không trang `/search` sẽ không có dữ liệu để trả về.

## Cài đặt & chạy
```bash
cd frontend
npm install
cp .env.example .env    # chỉnh VITE_API_BASE_URL nếu backend chạy port khác
npm run dev              # mở http://localhost:5173
```

## Các trang đã có
| Route | Chức năng |
|---|---|
| `/` | Trang chủ |
| `/login` | Đăng nhập — có sẵn nút điền nhanh 7 tài khoản test (khớp `app/seed.py` bên backend) |
| `/register` | Đăng ký (reputation mặc định = 1) |
| `/questions` | Danh sách câu hỏi + **tag cloud lọc theo tag** (click tag hoặc mở `?tag=...`) |
| `/questions/[id]` | Chi tiết câu hỏi: Upvote/Downvote, **danh sách câu trả lời** (xếp accepted lên đầu), **form đăng câu trả lời**, **nút "Chấp nhận"** (chỉ hiện cho tác giả câu hỏi), **bình luận** trên cả câu hỏi lẫn từng câu trả lời (tự disable nếu <50 rep và không phải bài của mình) |
| `/ask` | Form đặt câu hỏi mới (yêu cầu đăng nhập) |
| `/search` | **Tìm kiếm ngữ nghĩa** — nhập câu hỏi, chọn TF-IDF hoặc SBERT, xem % tương đồng + thời gian phản hồi |
| `/admin` | Chỉ hiện cho user `isAdmin=true`: quản lý user (khóa/mở khóa, chỉnh reputation tay), quản lý tag (sửa mô tả/xóa), nút **Reindex toàn bộ** + xem log benchmark thời gian phản hồi |

## Điểm quan trọng: UI phản ánh đúng cơ chế reputation-gated
File `src/lib/stores/auth.ts` định nghĩa lại đúng bảng `PRIVILEGE` khớp với backend
(`app/core/privileges.py`) để:
- Nút Upvote/Downvote tự disable + tooltip giải thích ngay trên UI khi chưa đủ điểm.
- Ô nhập bình luận tự disable + placeholder giải thích nếu <50 rep và không phải bài của mình
  (component `src/lib/components/CommentsSection.svelte`, dùng chung cho cả question và answer).
- Nút "Chấp nhận" câu trả lời chỉ hiện với tác giả câu hỏi (`isQuestionOwner` derived state).
- **Lưu ý:** đây chỉ là UX convenience — nguồn sự thật (source of truth) vẫn là backend,
  vì FE có thể bị bypass. Đã kiểm chứng bằng curl trực tiếp: backend vẫn chặn đúng theo
  `dev_e2e_test.py` (42/42 test PASS) dù không đi qua UI.

## Trang tìm kiếm (`/search`) — chi tiết
- 2 nút chuyển đổi TF-IDF / SBERT — đổi phương pháp sẽ tự chạy lại truy vấn hiện tại.
- Hiển thị `similarityPercent` (điểm tương đồng %) và `elapsedMs` (thời gian phản hồi) trả
  về từ backend — dùng trực tiếp để demo/chụp ảnh cho báo cáo so sánh 2 phương pháp.
- Nếu SBERT chưa sẵn sàng trên server (chưa cài `sentence-transformers` hoặc không có
  mạng để tải model), UI hiện thông báo rõ ràng thay vì lỗi khó hiểu (bắt lỗi HTTP 503).

## Cấu trúc thư mục (phần mới thêm)
```
src/
  lib/
    api/client.ts          # + answers/comments/tags/search/admin API functions
    components/
      CommentsSection.svelte  # component dùng chung cho comment trên question & answer
  routes/
    search/+page.svelte       # trang tìm kiếm TF-IDF/SBERT
    admin/+page.svelte         # trang quản trị (chỉ admin)
    questions/[id]/+page.svelte  # viết lại: + answers, accept-answer, comments
    questions/+page.svelte        # + tag cloud lọc theo tag
```

## Việc tiếp theo (theo đúng kế hoạch)
- Test toàn luồng thủ công với MongoDB thật + `sentence-transformers` cài đầy đủ (sandbox
  soạn code này không cài được `sentence-transformers`/MongoDB thật do giới hạn mạng —
  xem lưu ý trong `../backend-py/README.md`).
- Vẽ biểu đồ so sánh Precision@K / thời gian phản hồi từ `search_benchmark_log` cho báo cáo.
- Viết báo cáo, làm slide, quay demo dự phòng (Ngày 19-21).
