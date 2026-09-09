"""
Query Parser kiểu Stack Overflow - tách chuỗi tìm kiếm tự do thành các thành phần có cấu trúc.

Hỗ trợ cú pháp (lấy cảm hứng từ SO):
  "cụm từ"        -> phrase (khớp chuỗi con trong tiêu đề)
  [docker]        -> tag filter
  -elasticsearch  -> loại trừ term
  OR / AND        -> boolean (mặc định OR/AND implicit)
  score:5         -> voteScore >= 5
  score:0-4       -> range score
  answers:0       -> câu chưa có câu trả lời
  is:accepted     -> câu có accepted answer
  user:foo        -> tác giả có username/displayName chứa "foo"
  created:yyyy-mm-dd..yyyy-mm-dd -> khoảng thời gian tạo
  user:me         -> (dự phòng, xử lý ở router nếu có token)
Còn lại           -> text term cho TF-IDF cosine.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ParsedQuery:
    raw: str
    terms: list[str] = field(default_factory=list)       # vector terms (cho TF-IDF)
    phrases: list[str] = field(default_factory=list)     # cụm từ cần khớp substring trong tiêu đề
    exclude_terms: list[str] = field(default_factory=list)  # -term
    tags: list[str] = field(default_factory=list)        # [tag]
    score_min: float | None = None
    score_max: float | None = None
    answers: int | None = None                           # answers:N -> lọc chính xác (SO: 0 = unanswered)
    is_accepted: bool | None = None                      # is:accepted
    user: str | None = None                              # user:<name>
    created_start: datetime | None = None
    created_end: datetime | None = None

    @property
    def is_empty(self) -> bool:
        return not (
            self.terms or self.phrases or self.tags or self.exclude_terms
            or self.score_min is not None or self.score_max is not None
            or self.answers is not None or self.is_accepted is not None
            or self.user is not None
            or self.created_start is not None or self.created_end is not None
        )


# Phrase: chuỗi trong dấu nháy kép
_PHRASE_RE = re.compile(r'"([^"]+)"')
# Tag: [name]
_TAG_RE = re.compile(r"\[([^\]]+)\]")
# key:value — capture toàn bộ phần còn lại (có thể chứa unicode)
_KEYVAL_RE = re.compile(r"(^|\s)([a-zA-Z_]+):([^\s]+)")
# khoảng thời gian created:start..end
_CREATED_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.\.(\d{4}-\d{2}-\d{2})$")
# token thường (giữ token nhiều từ ghép sau khi đã bỏ phrase/tag)
_TOKEN_RE = re.compile(r"[A-Za-z0-9À-ỹà-ỹ_+#.\-]+")


def _parse_date(s: str) -> datetime:
    # mặc định theo cả ngày ở 00:00 UTC
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def parse_query(raw: str) -> ParsedQuery:
    """Tách câu query tự do thành ParsedQuery. Không ném exception."""
    raw = raw or ""
    pq = ParsedQuery(raw=raw)

    # 1) Bóc phrase trước (giữ nguyên, không tiền xử lý từ)
    work = raw
    phrases = _PHRASE_RE.findall(work)
    pq.phrases = [p.strip() for p in phrases if p.strip()]
    work = _PHRASE_RE.sub(" ", work)

    # 2) Bóc tag
    tags = _TAG_RE.findall(work)
    pq.tags = [t.lower().strip() for t in tags if t.strip()]
    work = _TAG_RE.sub(" ", work)

    # 3) Bóc key:value
    def _handle_keyval(key: str, val: str):
        k, v = key.lower(), val
        if k == "score":
            if ".." in v:
                a, b = v.split("..", 1)
                if a.isdigit():
                    pq.score_min = float(a)
                if b.isdigit():
                    pq.score_max = float(b)
            elif v.isdigit():
                pq.score_min = float(v)
            elif v.startswith(">"):
                pq.score_min = float(v[1:]) + 1 if v[1:].isdigit() else None
            elif v.startswith("<"):
                pq.score_max = float(v[1:]) - 1 if v[1:].isdigit() else None
            elif v.startswith(".."):
                pq.score_max = float(v[2:]) if v[2:].isdigit() else None
            elif v.endswith(".."):
                pq.score_min = float(v[:-2]) if v[:-2].isdigit() else None
        elif k == "answers":
            if v.isdigit():
                pq.answers = int(v)
        elif k == "is":
            if v == "accepted":
                pq.is_accepted = True
            elif v == "unaccepted":
                pq.is_accepted = False
        elif k == "user":
            # user:me được xử lý ở router (cần current_user); ở parser chỉ ghi token
            if v == "me":
                pq.user = "__me__"
            else:
                pq.user = v.lower()
        elif k == "created":
            m = _CREATED_RE.match(v)
            if m:
                pq.created_start = _parse_date(m.group(1))
                pq.created_end = _parse_date(m.group(2))
            else:
                # created:2024-01-01.. (mở) hoặc ..2024-06-30
                if v.endswith("..") and len(v) == len(v.rstrip(".")) and len(v) > 2:
                    try:
                        pq.created_start = _parse_date(v[:-2])
                    except ValueError:
                        pass
                elif v.startswith("..") and len(v) > 2:
                    try:
                        pq.created_end = _parse_date(v[2:])
                    except ValueError:
                        pass
        # các key khác bỏ qua

    def _keyval_finder(m: re.Match):
        _handle_keyval(m.group(2), m.group(3))
        return " "

    work = _KEYVAL_RE.sub(_keyval_finder, work)

    # 4) Còn lại -> tokens + dấu trừ loại trừ
    for tok in _TOKEN_RE.findall(work):
        if tok.startswith("-") and len(tok) > 1:
            pq.exclude_terms.append(tok[1:].lower())
        elif tok.lower() in ("or", "and"):
            continue  # bỏ boolean (mặc định implicit OR)
        else:
            lt = tok.lower()
            if lt and lt not in pq.terms:
                pq.terms.append(lt)

    return pq