"""
Tiền xử lý văn bản dùng chung cho TF-IDF (index lẫn query) - phải áp dụng CÙNG một hàm
cho cả lúc build chỉ mục và lúc encode câu truy vấn, nếu không vector sẽ lệch không gian.

Tiền xử lý áp dụng cho cả lúc build chỉ mục lẫn lúc encode truy vấn của mô hình TF-IDF.
"""
import re

# Thử dùng underthesea để tách từ tiếng Việt (ghép từ ghép: "học máy" -> 1 token thay vì 2)
# - nếu chưa cài (thư viện nặng), fallback về tách theo khoảng trắng, vẫn chạy được TF-IDF
# đúng thuật toán, chỉ là không gộp được từ ghép tiếng Việt.
try:
    from underthesea import word_tokenize as _vi_tokenize

    _HAS_UNDERTHESEA = True
except ImportError:  # pragma: no cover - môi trường không cài underthesea
    _HAS_UNDERTHESEA = False

# Stopword tối giản (tiếng Việt + tiếng Anh) - đủ dùng cho tiêu đề ngắn của câu hỏi kỹ thuật.
# Không loại các từ có thể mang nghĩa kỹ thuật (vd "là", "gì" giữ lại vì tiêu đề dạng câu hỏi
# rất ngắn, loại quá tay sẽ làm mất ngữ cảnh).
STOPWORDS = {
    "là", "của", "và", "các", "có", "được", "cho", "khi", "trong", "với", "để", "một",
    "này", "đó", "nên", "thì", "sẽ", "đã", "the", "a", "an", "is", "are", "to", "for",
    "of", "in", "on", "and", "or", "with", "how", "what", "do", "does",
}

_TOKEN_RE = re.compile(r"[a-zA-Z0-9À-ỹà-ỹ_+#.-]+", re.UNICODE)


def preprocess(text: str) -> list[str]:
    """
    Lowercase -> tokenize -> bỏ stopword. Trả về danh sách token (string).
    Giữ lại các ký tự kỹ thuật như '.', '+', '#' trong token (vd "node.js", "c#", "c++")
    vì đây là các thuật ngữ có ý nghĩa riêng, tách rời sẽ mất thông tin.
    """
    text = text.lower().strip()
    if _HAS_UNDERTHESEA:
        try:
            text = _vi_tokenize(text, format="text")  # ghép từ ghép tiếng Việt bằng "_"
        except Exception:
            pass  # nếu underthesea lỗi bất thường trên input lạ, vẫn tiếp tục bằng regex thô

    tokens = _TOKEN_RE.findall(text)
    tokens = [t.strip(".-") for t in tokens if t.strip(".-")]
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return tokens


def preprocess_joined(text: str) -> str:
    """Trả về chuỗi token đã nối bằng khoảng trắng - tiện cho TfidfVectorizer(analyzer='word')."""
    return " ".join(preprocess(text))
