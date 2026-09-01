# Đặc tả yêu cầu — Hệ thống Quản trị tri thức trên Website

> **Stack Overflow Clone** tích hợp Tìm kiếm theo tiêu đề bằng TF-IDF
> Phiên bản: 1.0 (đã phê chuẩn)

---

## Theo dõi phiên bản tài liệu

| Tên | Ngày | Lý do thay đổi | Phiên bản |
|---|---|---|---|
| Đặc tả yêu cầu Hệ thống Quản trị tri thức | ..../..../........ | Tạo mới | 1.0 |

---

## 1. Giới thiệu

### 1.1 Mục tiêu

Tài liệu này lập ra nhằm cho các thành viên có cái nhìn toàn diện về phần mềm.

Các nhóm người sử dụng tài liệu:

- **Thiết kế viên (Dev):** dựa vào tài liệu để thiết kế dữ liệu, giao diện, kiến trúc và các thành phần.
- **Kiểm thử viên (QA):** dựa vào tài liệu để biết được chức năng và các vấn đề cần kiểm thử.
- **Người quản lý:** dựa vào tài liệu để kiểm soát, quản lý các nhóm chức năng, các ràng buộc và yêu cầu phần mềm.

### 1.2 Phạm vi sản phẩm

- Sản phẩm Website Quản trị tri thức phục vụ cho việc đặt câu hỏi, trả lời, thảo luận và tra cứu lại kiến thức kỹ thuật đã có sẵn trong một tổ chức, hoạt động theo mô hình tương tự Stack Overflow.
- Áp dụng cho các tổ chức, công ty công nghệ, cộng đồng lập trình viên có nhu cầu lưu trữ và chia sẻ tri thức nội bộ một cách có hệ thống.
- Phần mềm hoạt động trên nền tảng web; trình duyệt web từ các thiết bị người dùng giao tiếp với máy chủ web thông qua giao thức truyền dẫn siêu văn bản dựa trên TCP/IP.
- **Chức năng đặc thù:** tìm kiếm câu hỏi theo tiêu đề dựa trên mức độ tương đồng (Vector Space Model, trọng số TF-IDF, đo bằng Cosine Similarity) thay vì so khớp chuỗi ký tự thông thường.

### 1.3 Bảng chú giải thuật ngữ

| STT | Thuật ngữ/từ viết tắt | Định nghĩa, giải thích |
|---|---|---|
| 1 | CSDL | Cơ sở dữ liệu |
| 2 | HTTP | Giao thức truyền tải siêu văn bản |
| 3 | Client | Máy trạm, được sử dụng bởi người dùng |
| 4 | Server/Máy chủ | Một loại máy tính nhận, chuyển hoặc lưu trữ dữ liệu, chương trình bằng cách liên kết với các máy tính khác thông qua mạng internet |
| 5 | Web browser | Trình duyệt web |
| 6 | User | Người sử dụng |
| 7 | Reputation | Điểm uy tín tích lũy được từ các đóng góp có ích, quyết định quyền hạn của thành viên trong hệ thống |
| 8 | TF-IDF | Term Frequency – Inverse Document Frequency, kỹ thuật đánh trọng số từ trong mô hình không gian vector |
| 9 | Cosine Similarity | Độ đo tương đồng giữa hai vector, dùng để xếp hạng kết quả tìm kiếm |
| 10 | GUI | Graphic User Interface — giao diện người dùng |

### 1.4 Tài liệu tham khảo

- TS Huỳnh Xuân Hiệp và Ths Phan Phương Lan, *Giáo trình nhập môn Công nghệ phần mềm*, Đại học Cần Thơ, 2011.
- Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press.
- Stack Overflow. *Stack Exchange reputation privileges*. https://stackoverflow.com/help/privileges
- Mẫu tài liệu đặc tả: https://elcit.ctu.edu.vn/course/view.php?id=2232

### 1.5 Bố cục tài liệu

Tài liệu Đặc tả yêu cầu phần mềm viết nhằm cung cấp thông tin về phần mềm được phát triển. Tài liệu này gồm 4 phần: giới thiệu, mô tả tổng quan, các yêu cầu giao tiếp bên ngoài, và các tính năng của hệ thống (bao gồm cả các yêu cầu phi chức năng).

- **Phần 1 — Giới thiệu:** mục tiêu tài liệu, nhóm người dùng tài liệu, phạm vi sản phẩm, bảng chú giải thuật ngữ và tài liệu tham khảo.
- **Phần 2 — Mô tả tổng quan:** bối cảnh ra đời, lợi ích sản phẩm mang lại, các tính năng tổng quát, đặc điểm nhóm người dùng, môi trường vận hành.
- **Phần 3 — Các yêu cầu giao tiếp bên ngoài:** đặc điểm giao tiếp giữa phần mềm với người dùng, phần cứng, phần mềm.
- **Phần 4 — Các tính năng của hệ thống:** tổ chức yêu cầu chức năng theo từng tính năng, kèm yêu cầu phi chức năng và quy tắc nghiệp vụ.

---

## 2. Mô tả tổng quan

### 2.1 Bối cảnh của sản phẩm

Trong một tổ chức — có thể là một công ty công nghệ, một trường học hay một cộng đồng lập trình viên — kiến thức và kinh nghiệm thường bị phân tán ở nhiều nơi khác nhau: người này biết cách xử lý một lỗi kỹ thuật nhưng không ai khác biết, người khác đã từng gặp một vấn đề tương tự nhưng không có nơi nào để ghi lại.

Một số công cụ hỗ trợ trao đổi hiện nay như chat nhóm, email... hoạt động khá rời rạc, thông tin dễ bị trôi và khó tra cứu lại về sau. Điều này gây khó khăn cho những người có nhu cầu tìm lại một giải pháp đã từng được thảo luận trước đó.

Nắm được nhu cầu đó, nhóm mong muốn xây dựng và phát triển một Website hoạt động theo mô hình Stack Overflow, hỗ trợ đặt câu hỏi, trả lời, thảo luận và đặc biệt là tra cứu lại kiến thức đã có sẵn một cách nhanh chóng thông qua chức năng tìm kiếm thông minh theo tiêu đề.

### 2.2 Các chức năng của sản phẩm

- Đăng ký tài khoản
- Đăng nhập
- Tìm kiếm câu hỏi theo tiêu đề (TF-IDF)
- Đặt câu hỏi
- Trả lời câu hỏi
- Bình luận
- Bỏ phiếu (Upvote/Downvote)
- Sửa/Xóa bài viết
- Quản lý tài khoản cá nhân
- Quản lý người dùng
- Quản lý thẻ (tag) hệ thống

### 2.3 Đặc điểm người sử dụng

| Nhóm người sử dụng | Đặc trưng | Các chức năng | Vai trò | Quyền hạn | Mức độ quan trọng |
|---|---|---|---|---|---|
| Khách (chưa đăng nhập) | Người ngoài, chưa có tài khoản, muốn tham khảo nội dung có sẵn | - Xem danh sách câu hỏi<br>- Tìm kiếm câu hỏi<br>- Đăng ký tài khoản | Khách | Guest | Ít quan trọng |
| Thành viên | Người dùng đã đăng ký, quyền hạn mở rộng dần theo điểm uy tín (reputation) tích lũy được | - Đăng nhập<br>- Đặt câu hỏi, trả lời<br>- Bình luận, bỏ phiếu<br>- Sửa/xóa bài (theo reputation)<br>- Quản lý tài khoản cá nhân | Người dùng | Member | Rất quan trọng |
| Quản trị viên | Tài khoản cố định (không qua reputation), am hiểu vận hành hệ thống | - Đăng nhập<br>- Quản lý người dùng<br>- Quản lý thẻ hệ thống<br>- Theo dõi module tìm kiếm | Admin | Admin | Quan trọng |

### 2.4 Môi trường vận hành

**Server:**

- Hệ điều hành: Linux (Ubuntu 22.04 trở lên) hoặc Windows Server 2019 trở lên
- Hệ CSDL: MongoDB 6.0 trở lên
- RAM: tối thiểu 4GB (cần đủ để cache vocabulary và vector TF-IDF trong bộ nhớ)
- Ổ cứng: tối thiểu 50GB

**Client:**

- Trình duyệt hỗ trợ HTML5/JavaScript hiện đại (Chrome, Firefox, Edge phiên bản gần đây)
- Độ phân giải màn hình: 1024x720 trở lên

### 2.5 Các ràng buộc về thực thi và thiết kế

- Ngôn ngữ lập trình backend: **Python (FastAPI)**
- Ngôn ngữ lập trình frontend: **TypeScript/Svelte (SvelteKit)**
- Hệ quản trị CSDL: **MongoDB**
- Thời gian phản hồi tìm kiếm phải nhỏ hơn 1 giây
- Giao diện đơn giản, thân thiện với người sử dụng
- Phần mềm chạy ổn định trên nền web

### 2.6 Các giả định và phụ thuộc

- Máy tính người dùng hỗ trợ kết nối internet và trình duyệt web hiện đại
- Hệ thống đã có chức năng xây dựng lại chỉ mục tìm kiếm (reindex) định kỳ hoặc theo yêu cầu quản trị viên

---

## 3. Các yêu cầu giao tiếp bên ngoài

### 3.1 Giao diện người sử dụng

- Font chữ: hệ thống dùng font sans-serif hiện đại, dễ đọc trên màn hình
- Màu sắc: hài hòa, tối giản, tương phản tốt cho các nội dung dạng văn bản kỹ thuật (code, câu hỏi, câu trả lời)
- Giao diện trang chủ hiển thị danh sách câu hỏi mới nhất, ô tìm kiếm nổi bật ở đầu trang
- Các thành phần cần giao diện riêng: đăng nhập/đăng ký, danh sách câu hỏi, chi tiết câu hỏi kèm câu trả lời, soạn câu hỏi/câu trả lời, hồ sơ cá nhân, trang quản trị

### 3.2 Giao tiếp phần cứng

- Người dùng thao tác với hệ thống bằng chuột và bàn phím
- Không yêu cầu thiết bị phần cứng đặc biệt khác

### 3.3 Giao tiếp phần mềm

- Sử dụng hệ quản trị CSDL **MongoDB**
- Sử dụng thư viện **scikit-learn** để xây dựng và tính toán vector TF-IDF
- Hệ điều hành máy chủ: Linux hoặc Windows Server

### 3.4 Giao tiếp truyền thông tin

- Người dùng tương tác với hệ thống thông qua trình duyệt web (Web browser)
- Sử dụng giao thức HTTP/HTTPS dựa trên TCP/IP để truyền và nhận dữ liệu giữa máy chủ và các máy client
- API nội bộ giữa frontend và backend giao tiếp theo chuẩn **RESTful**, dữ liệu định dạng **JSON**

---

## 4. Các tính năng của hệ thống

> Sơ đồ Use Case tổng quát của hệ thống được trình bày ở Phụ lục A. Mỗi tính năng dưới đây được mô tả chi tiết theo mẫu đặc tả Use Case, gồm: actor tham gia, mức độ cần thiết, mối quan hệ với các use case khác, và luồng xử lý.

### 4.1 UC001 — Đăng ký tài khoản

| | |
|---|---|
| **Actor chính** | Khách |
| **Mức độ cần thiết** | Bắt buộc |
| **Phân loại** | Đơn giản |
| **Mối quan tâm** | Khách muốn đăng ký tài khoản để có thể đặt câu hỏi, trả lời và tham gia thảo luận trong hệ thống. |
| **Mô tả tóm tắt** | Cho phép Khách đăng ký để trở thành Thành viên của hệ thống. |
| **Trigger** | Khi khách có nhu cầu tạo tài khoản để sử dụng đầy đủ chức năng của hệ thống (external) |
| **Quan hệ** | Association: Khách |

**Luồng xử lý bình thường:**

1. Khách click vào nút "Đăng ký" trên trang chủ.
2. Hệ thống hiển thị form đăng ký yêu cầu nhập username, email, mật khẩu.
3. Khách nhập đầy đủ thông tin và click nút "Đăng ký".
4. Hệ thống kiểm tra tính hợp lệ và trùng lặp của username/email.
5. Hệ thống lưu thông tin tài khoản mới vào cơ sở dữ liệu với điểm reputation khởi tạo = 1, thông báo đăng ký thành công.
6. Chuyển về giao diện đăng nhập, kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 4: Nếu username hoặc email đã tồn tại, hệ thống thông báo lỗi và yêu cầu khách nhập lại.

---

### 4.2 UC002 — Đăng nhập

| | |
|---|---|
| **Actor chính** | Khách, Thành viên, Quản trị viên |
| **Mức độ cần thiết** | Bắt buộc |
| **Phân loại** | Đơn giản |
| **Mối quan tâm** | Người dùng (Thành viên, Quản trị viên) muốn đăng nhập để sử dụng các chức năng yêu cầu xác thực của hệ thống. |
| **Mô tả tóm tắt** | Cho phép người dùng đăng nhập vào hệ thống bằng username và mật khẩu. |
| **Trigger** | Khi người dùng có nhu cầu đăng nhập để tương tác với hệ thống (external) |
| **Quan hệ** | Association: Thành viên, Quản trị viên. Include: được bao gồm bởi các use case Đặt câu hỏi, Trả lời câu hỏi, Bình luận, Bỏ phiếu, Sửa/Xóa bài viết, Quản lý tài khoản cá nhân, Quản lý người dùng, Quản lý thẻ hệ thống |

**Luồng xử lý bình thường:**

1. User click vào nút "Đăng nhập" trên trang chủ.
2. Hệ thống hiển thị form đăng nhập.
3. User nhập username và mật khẩu, sau đó click nút "Đăng nhập".
4. Hệ thống kiểm tra username, mật khẩu (mã hoá bcrypt) và cấp JWT token, xác định quyền hạn theo điểm reputation/cờ isAdmin.
5. Hệ thống chuyển sang giao diện với các chức năng tuỳ theo quyền hạn của user.
6. Kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 4: Nếu username hoặc mật khẩu không chính xác, hệ thống thông báo lỗi và yêu cầu user nhập lại.

---

### 4.3 UC003 — Tìm kiếm câu hỏi theo tiêu đề (TF-IDF)

> Đây là chức năng đặc thù của đề tài, cho phép tìm kiếm câu hỏi theo mức độ tương đồng ngữ nghĩa dựa trên mô hình không gian vector (Vector Space Model) với trọng số TF-IDF, thay vì so khớp chuỗi ký tự thông thường.

| | |
|---|---|
| **Actor chính** | Khách, Thành viên |
| **Mức độ cần thiết** | Bắt buộc |
| **Phân loại** | Phức tạp |
| **Mối quan tâm** | Người dùng muốn tra cứu nhanh xem đã có câu hỏi nào tương tự vấn đề mình đang gặp phải hay chưa. |
| **Mô tả tóm tắt** | Người dùng nhập từ khóa, hệ thống vector hóa từ khóa và so khớp với vector TF-IDF đã lập chỉ mục cho từng tiêu đề câu hỏi, trả về danh sách sắp xếp theo độ tương đồng Cosine giảm dần. |
| **Trigger** | Khi người dùng nhập từ khóa vào ô tìm kiếm (external) |
| **Quan hệ** | Association: Khách, Thành viên. Extend: mở rộng của use case Xem danh sách câu hỏi |

**Luồng xử lý bình thường:**

1. Người dùng nhập từ khóa vào ô tìm kiếm trên thanh điều hướng.
2. Hệ thống tiền xử lý câu truy vấn (chuyển chữ thường, tách từ, bỏ stop-word).
3. Hệ thống vector hóa câu truy vấn theo đúng vocabulary TF-IDF đã dùng lúc lập chỉ mục.
4. Hệ thống tính độ tương đồng Cosine giữa vector truy vấn và toàn bộ vector tiêu đề đã lưu trong bộ nhớ.
5. Hệ thống sắp xếp kết quả theo độ tương đồng giảm dần và trả về top-K câu hỏi liên quan nhất, kèm điểm tương đồng (%).
6. Người dùng click vào một câu hỏi trong kết quả để xem chi tiết. Kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 5: Nếu không có câu hỏi nào có độ tương đồng lớn hơn 0, hệ thống hiển thị thông báo "Không tìm thấy kết quả phù hợp" và gợi ý đặt câu hỏi mới.

**Ghi chú kỹ thuật (hiệu năng thực nghiệm):**

- Thời gian phản hồi tìm kiếm trung bình trên 5.969 câu hỏi: **11,98ms**
- Thời gian reindex toàn bộ dữ liệu (5.969 câu hỏi): **346,8ms**
- Collection lưu vector chỉ mục: `question_vectors_tfidf` (tách riêng khỏi collection câu hỏi chính)

---

### 4.4 UC004 — Đặt câu hỏi

| | |
|---|---|
| **Actor chính** | Thành viên |
| **Mức độ cần thiết** | Bắt buộc |
| **Phân loại** | Trung bình |
| **Mối quan tâm** | Thành viên (điểm reputation ≥ 1) muốn đặt một câu hỏi mới vì chưa tìm thấy câu hỏi tương tự trong hệ thống. |
| **Mô tả tóm tắt** | Cho phép Thành viên tạo một câu hỏi mới, gồm tiêu đề, nội dung và gắn thẻ (tag) chủ đề. |
| **Trigger** | Khi Thành viên không tìm thấy câu hỏi phù hợp và muốn đặt câu hỏi mới (external) |
| **Quan hệ** | Association: Thành viên. Include: Gắn thẻ (tag) cho câu hỏi |

**Luồng xử lý bình thường:**

1. Thành viên (đã đăng nhập) click vào nút "Đặt câu hỏi".
2. Hệ thống hiển thị form nhập tiêu đề, nội dung và thẻ (tag) liên quan.
3. Thành viên nhập đầy đủ thông tin và click nút "Đăng câu hỏi".
4. Hệ thống kiểm tra điểm reputation của Thành viên (≥ 1) và tính hợp lệ của dữ liệu nhập vào.
5. Hệ thống lưu câu hỏi vào cơ sở dữ liệu với cờ `isIndexed = false`, cập nhật `questionCount` cho các tag liên quan.
6. Hệ thống lập chỉ mục TF-IDF cho tiêu đề câu hỏi mới, cập nhật `isIndexed = true`.
7. Hệ thống chuyển sang trang chi tiết câu hỏi vừa tạo. Kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 4: Nếu điểm reputation của Thành viên nhỏ hơn 1, hệ thống từ chối và thông báo yêu cầu điểm tối thiểu.
- Bước 4: Nếu tiêu đề hoặc nội dung để trống, hệ thống thông báo lỗi và yêu cầu nhập lại.

---

### 4.5 UC005 — Trả lời câu hỏi

| | |
|---|---|
| **Actor chính** | Thành viên |
| **Mức độ cần thiết** | Bắt buộc |
| **Phân loại** | Đơn giản |
| **Mối quan tâm** | Thành viên (điểm reputation ≥ 1) muốn chia sẻ giải pháp cho một câu hỏi đã có trong hệ thống. |
| **Mô tả tóm tắt** | Cho phép Thành viên viết câu trả lời cho một câu hỏi. |
| **Trigger** | Khi Thành viên xem một câu hỏi thuộc lĩnh vực mình am hiểu và muốn trả lời (external) |
| **Quan hệ** | Association: Thành viên |

**Luồng xử lý bình thường:**

1. Thành viên xem chi tiết một câu hỏi, click vào ô "Viết câu trả lời".
2. Thành viên nhập nội dung câu trả lời và click nút "Gửi câu trả lời".
3. Hệ thống kiểm tra điểm reputation của Thành viên (≥ 1) và tính hợp lệ của nội dung.
4. Hệ thống lưu câu trả lời vào cơ sở dữ liệu, liên kết với câu hỏi tương ứng.
5. Hệ thống hiển thị câu trả lời mới trong danh sách câu trả lời của câu hỏi đó. Kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 3: Nếu điểm reputation của Thành viên nhỏ hơn 1, hệ thống từ chối và thông báo yêu cầu điểm tối thiểu.

---

### 4.6 UC006 — Bình luận

| | |
|---|---|
| **Actor chính** | Thành viên |
| **Mức độ cần thiết** | Tùy chọn |
| **Phân loại** | Đơn giản |
| **Mối quan tâm** | Thành viên muốn bổ sung ý kiến ngắn vào một câu hỏi hoặc câu trả lời. |
| **Mô tả tóm tắt** | Cho phép Thành viên viết bình luận vào bài viết của chính mình (reputation ≥ 1) hoặc của người khác (reputation ≥ 50). |
| **Trigger** | Khi Thành viên muốn bổ sung, làm rõ hoặc góp ý cho một câu hỏi/câu trả lời (external) |
| **Quan hệ** | Association: Thành viên |

**Luồng xử lý bình thường:**

1. Thành viên click vào nút "Thêm bình luận" dưới một câu hỏi hoặc câu trả lời.
2. Thành viên nhập nội dung bình luận và click nút "Gửi".
3. Hệ thống kiểm tra điểm reputation: ≥ 1 nếu bình luận vào bài của chính mình, ≥ 50 nếu bình luận vào bài người khác.
4. Hệ thống lưu bình luận và liên kết với đối tượng (câu hỏi/câu trả lời) tương ứng.
5. Hệ thống hiển thị bình luận mới. Kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 3: Nếu điểm reputation không đủ theo điều kiện, hệ thống từ chối và thông báo ngưỡng điểm cần thiết.

---

### 4.7 UC007 — Bỏ phiếu (Upvote/Downvote)

| | |
|---|---|
| **Actor chính** | Thành viên |
| **Mức độ cần thiết** | Tùy chọn |
| **Phân loại** | Đơn giản |
| **Mối quan tâm** | Thành viên muốn đánh giá chất lượng một câu hỏi/câu trả lời bằng cách upvote hoặc downvote. |
| **Mô tả tóm tắt** | Cho phép Thành viên bỏ phiếu thuận (upvote, reputation ≥ 15) hoặc phiếu chống (downvote, reputation ≥ 125) cho câu hỏi/câu trả lời, đồng thời cộng/trừ điểm reputation của tác giả. |
| **Trigger** | Khi Thành viên đọc và muốn đánh giá một câu hỏi/câu trả lời (external) |
| **Quan hệ** | Association: Thành viên |

**Luồng xử lý bình thường:**

1. Thành viên click vào nút mũi tên lên (upvote) hoặc xuống (downvote) cạnh câu hỏi/câu trả lời.
2. Hệ thống kiểm tra điểm reputation của Thành viên tương ứng với loại vote (≥ 15 cho upvote, ≥ 125 cho downvote).
3. Hệ thống kiểm tra Thành viên chưa từng vote cho đối tượng này.
4. Hệ thống ghi nhận phiếu bầu, cập nhật `voteScore` của câu hỏi/câu trả lời và điểm reputation của tác giả.
5. Hệ thống cập nhật giao diện hiển thị số điểm mới. Kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 2: Nếu điểm reputation không đủ, hệ thống từ chối và thông báo ngưỡng điểm cần thiết.
- Bước 3: Nếu Thành viên đã vote trước đó, hệ thống cho phép hủy hoặc đổi chiều phiếu bầu thay vì tạo phiếu mới.

---

### 4.8 UC008 — Sửa/Xóa bài viết

| | |
|---|---|
| **Actor chính** | Thành viên |
| **Mức độ cần thiết** | Tùy chọn |
| **Phân loại** | Trung bình |
| **Mối quan tâm** | Thành viên muốn chỉnh sửa nội dung bài viết của chính mình, hoặc sửa/xóa bài viết của người khác khi phát hiện sai sót/vi phạm (cần điểm reputation cao). |
| **Mô tả tóm tắt** | Cho phép: (a) Thành viên sửa bài viết của chính mình không giới hạn điểm reputation; (b) sửa bài viết của người khác khi reputation ≥ 500; (c) xóa câu hỏi của người khác khi reputation ≥ 2000. |
| **Trigger** | Khi Thành viên cần cập nhật hoặc gỡ bỏ một bài viết (external) |
| **Quan hệ** | Association: Thành viên. Extend: mở rộng của use case Bỏ phiếu (đối với chức năng xóa) |

**Luồng xử lý bình thường:**

1. Thành viên click vào nút "Sửa" hoặc "Xóa" trên một câu hỏi/câu trả lời.
2. Hệ thống kiểm tra: nếu là tác giả thì cho phép sửa trực tiếp; nếu không phải tác giả thì kiểm tra điểm reputation (≥ 500 để sửa, ≥ 2000 để xóa câu hỏi).
3. Nếu là sửa: hệ thống hiển thị form với nội dung hiện tại, Thành viên chỉnh sửa và click "Lưu".
4. Nếu là xóa: hệ thống hiển thị hộp thoại xác nhận, Thành viên xác nhận "Xóa".
5. Hệ thống cập nhật/xóa dữ liệu tương ứng trong cơ sở dữ liệu và (nếu là câu hỏi) đánh dấu cần lập lại chỉ mục tìm kiếm.
6. Hệ thống hiển thị kết quả cập nhật. Kết thúc use case.

**Luồng luân phiên/đặc biệt:**

- Bước 2: Nếu Thành viên không phải tác giả và điểm reputation không đủ, hệ thống từ chối thao tác.

---

### 4.9 UC009 — Quản lý tài khoản cá nhân

| | |
|---|---|
| **Actor chính** | Thành viên |
| **Mức độ cần thiết** | Bắt buộc |
| **Phân loại** | Đơn giản |
| **Mối quan tâm** | Thành viên muốn xem hoặc cập nhật thông tin hồ sơ cá nhân, theo dõi điểm uy tín và lịch sử đóng góp. |
| **Mô tả tóm tắt** | Cho phép Thành viên xem hồ sơ, lịch sử reputation (`reputationLog`), danh sách câu hỏi/câu trả lời đã đóng góp, và cập nhật thông tin cá nhân. |
| **Trigger** | Khi Thành viên muốn xem/kiểm tra thông tin cá nhân (external) |
| **Quan hệ** | Association: Thành viên |

**Luồng xử lý bình thường:**

1. Thành viên click vào tên/avatar của mình để vào trang hồ sơ cá nhân.
2. Hệ thống hiển thị thông tin: điểm reputation hiện tại, lịch sử thay đổi điểm, danh sách câu hỏi và câu trả lời đã đóng góp.
3. Nếu muốn cập nhật thông tin, Thành viên click "Chỉnh sửa hồ sơ", nhập thông tin mới và lưu.
4. Hệ thống cập nhật thông tin vào cơ sở dữ liệu. Kết thúc use case.

**Luồng luân phiên/đặc biệt:** Không có.

---

### 4.10 UC010 — Quản lý người dùng

| | |
|---|---|
| **Actor chính** | Quản trị viên |
| **Mức độ cần thiết** | Bắt buộc |
| **Phân loại** | Trung bình |
| **Mối quan tâm** | Quản trị viên cần theo dõi, khóa tài khoản vi phạm hoặc điều chỉnh điểm reputation của người dùng khi cần thiết. |
| **Mô tả tóm tắt** | Cho phép Quản trị viên xem danh sách người dùng, khóa/mở khóa tài khoản và điều chỉnh điểm reputation. |
| **Trigger** | Khi Quản trị viên cần xử lý một tài khoản vi phạm hoặc rà soát hệ thống (external) |
| **Quan hệ** | Association: Quản trị viên |

**Luồng xử lý bình thường:**

1. Quản trị viên vào trang "Quản lý người dùng" trong khu vực quản trị.
2. Hệ thống hiển thị danh sách người dùng kèm điểm reputation, trạng thái tài khoản.
3. Quản trị viên chọn một người dùng, chọn thao tác (khóa/mở khóa tài khoản, hoặc điều chỉnh điểm reputation).
4. Hệ thống hiển thị hộp thoại xác nhận; Quản trị viên xác nhận thao tác.
5. Hệ thống cập nhật trạng thái/điểm số của tài khoản trong cơ sở dữ liệu. Kết thúc use case.

**Luồng luân phiên/đặc biệt:** Không có.

---

### 4.11 UC011 — Quản lý thẻ (tag) hệ thống

| | |
|---|---|
| **Actor chính** | Quản trị viên |
| **Mức độ cần thiết** | Tùy chọn |
| **Phân loại** | Đơn giản |
| **Mối quan tâm** | Quản trị viên cần duy trì hệ thống thẻ chủ đề gọn gàng, tránh trùng lặp. |
| **Mô tả tóm tắt** | Cho phép Quản trị viên xem danh sách thẻ (tag), gộp các thẻ trùng lặp/tương tự, hoặc tạo mới thẻ chuẩn cho hệ thống. |
| **Trigger** | Khi Quản trị viên phát hiện thẻ trùng lặp hoặc cần chuẩn hóa danh mục chủ đề (external) |
| **Quan hệ** | Association: Quản trị viên |

**Luồng xử lý bình thường:**

1. Quản trị viên vào trang "Quản lý thẻ" trong khu vực quản trị.
2. Hệ thống hiển thị danh sách thẻ kèm số lượng câu hỏi (`questionCount`) sử dụng mỗi thẻ.
3. Quản trị viên chọn thao tác: tạo thẻ mới, đổi tên thẻ, hoặc gộp hai thẻ trùng lặp.
4. Hệ thống cập nhật danh sách thẻ và cập nhật lại tham chiếu `tag[]` trong các câu hỏi liên quan.
5. Kết thúc use case.

**Luồng luân phiên/đặc biệt:** Không có.

---

## 4.12 Các yêu cầu phi chức năng

### 4.13 Yêu cầu thực thi

- Hệ thống phải đảm bảo khả năng đáp ứng cho tối thiểu **50 người dùng truy cập đồng thời**.
- Thời gian phản hồi cho một lượt tìm kiếm (TF-IDF) phải **nhỏ hơn 1 giây**; thực nghiệm thực tế trên 5.969 câu hỏi cho thời gian phản hồi trung bình **11,98ms**.
- Thời gian xây dựng lại chỉ mục tìm kiếm (reindex) cho toàn bộ dữ liệu phải đủ nhanh để có thể chạy định kỳ mà không ảnh hưởng trải nghiệm người dùng (thực nghiệm: **346,8ms** cho 5.969 câu hỏi).

### 4.14 Yêu cầu an toàn

- Dữ liệu phải được sao lưu định kỳ (khuyến nghị 1 tuần/lần) và lưu trữ an toàn đề phòng sự cố hệ thống.
- Mật khẩu người dùng phải được băm (hash) bằng **bcrypt** trước khi lưu trữ, không lưu plaintext.
- Phiên đăng nhập sử dụng **JWT** có thời hạn, truyền qua kết nối HTTPS.

### 4.15 Yêu cầu bảo mật

- Chỉ các đối tượng có phân quyền tương ứng (theo điểm reputation hoặc cờ `isAdmin`) mới được phép thực hiện các thao tác nhạy cảm (sửa/xóa bài người khác, quản lý người dùng).
- Các chức năng hiển thị trên giao diện phải dựa trên đúng quyền hạn hiện tại của người dùng.
- Hệ thống phải chống được các tấn công cơ bản như **SQL/NoSQL Injection**, **XSS** thông qua việc kiểm tra và làm sạch dữ liệu đầu vào.

### 4.16 Các đặc điểm chất lượng phần mềm

- **Tính sẵn sàng:** phải đạt mức 99% theo năm (không tính thời gian bảo trì).
- **Khả năng phục hồi:** trong trường hợp xảy ra sự cố, thời gian cho phép hệ thống phục hồi trạng thái bình thường là **4 giờ**.
- **Khả năng mở rộng:** kiến trúc tách riêng collection lưu vector chỉ mục (`question_vectors_tfidf`) khỏi dữ liệu câu hỏi chính, cho phép nâng cấp cơ chế tìm kiếm trong tương lai mà không ảnh hưởng dữ liệu gốc.

### 4.17 Các quy tắc nghiệp vụ

1. Mỗi nhóm người dùng chỉ được thực hiện đúng các chức năng theo quyền hạn của mình.
2. Quyền hạn của Thành viên (bình luận vào bài người khác, downvote, sửa bài người khác, xóa câu hỏi người khác) được mở dần theo điểm reputation tích lũy, không được cấp cố định.
3. Quản trị viên là tài khoản cố định, không tham gia cơ chế tích lũy reputation để nhận quyền quản trị.
4. Mỗi người dùng có tài khoản đăng nhập riêng; phiên làm việc hết hạn sau một khoảng thời gian không hoạt động.
5. Câu hỏi mới hoặc được chỉnh sửa phải được lập lại chỉ mục tìm kiếm trước khi xuất hiện trong kết quả tìm kiếm theo tiêu đề.

**Bảng ngưỡng reputation (tổng hợp để dev tra cứu nhanh):**

| Hành động | Ngưỡng reputation tối thiểu |
|---|---|
| Đặt câu hỏi / Trả lời câu hỏi | ≥ 1 |
| Bình luận vào bài của chính mình | ≥ 1 |
| Bình luận vào bài của người khác | ≥ 50 |
| Upvote | ≥ 15 |
| Downvote | ≥ 125 |
| Sửa bài viết của người khác | ≥ 500 |
| Xóa câu hỏi của người khác | ≥ 2000 |
| Tài khoản mới khi đăng ký | = 1 (mặc định) |

---

## Phụ lục A: Các mô hình phân tích

- Hình 1: Sơ đồ Use Case tổng quát của hệ thống *(xem file gốc .docx để xem hình)*
- Hình 2: Sơ đồ quan hệ (ERD) giữa các collection MongoDB *(xem file gốc .docx để xem hình)*

---

## Phụ lục B: Giải thích một số thuật ngữ kỹ thuật

**Bộ giao thức TCP/IP**
TCP/IP (Internet Protocol Suite — Bộ giao thức liên mạng) là một bộ các giao thức truyền thông mà Internet và hầu hết các mạng máy tính thương mại đang chạy trên đó, được đặt tên theo hai giao thức chính TCP (Transmission Control Protocol) và IP (Internet Protocol).

**Mô hình không gian vector (Vector Space Model) và TF-IDF**
Là mô hình biểu diễn văn bản dưới dạng vector số thực trong không gian nhiều chiều, mỗi chiều ứng với một từ trong tập từ vựng. TF-IDF (Term Frequency – Inverse Document Frequency) là cách đánh trọng số cho mỗi từ: TF đo tần suất xuất hiện của từ trong văn bản, IDF đo mức độ hiếm gặp của từ đó trong toàn bộ tập văn bản — từ càng hiếm càng có trọng số cao vì mang tính đặc trưng.

**Cosine Similarity**
Là độ đo mức độ tương đồng giữa hai vector dựa trên góc giữa chúng, được tính bằng tích vô hướng của hai vector chia cho tích độ dài (norm) của chúng. Giá trị càng gần 1 nghĩa là hai vector (ở đây là từ khóa và tiêu đề câu hỏi) càng giống nhau.

---

## Tóm tắt kỹ thuật nhanh cho team code

| Hạng mục | Lựa chọn |
|---|---|
| Backend | Python (FastAPI) |
| Frontend | TypeScript / Svelte (SvelteKit) |
| CSDL | MongoDB ≥ 6.0 |
| Thuật toán tìm kiếm | TF-IDF (scikit-learn) + Cosine Similarity |
| Xác thực | JWT (qua HTTPS) |
| Mã hóa mật khẩu | bcrypt |
| Giao tiếp API | RESTful, JSON |
| Collection index riêng | `question_vectors_tfidf` |
| SLA thời gian phản hồi tìm kiếm | < 1 giây (thực nghiệm ~12ms) |
| Số user đồng thời tối thiểu | 50 |
| Tính sẵn sàng | 99%/năm |
| RTO khi sự cố | 4 giờ |
