"""
Test end-to-end TOÀN BỘ luồng nghiệp vụ bằng DB giả lập (mongomock-motor) -
không cần MongoDB server thật. Dùng để tự kiểm tra logic trước khi giao nộp.

Chạy: ./venv/bin/python -m app.dev_e2e_test
"""
import asyncio
import sys

# Patch database TRƯỚC khi import bất kỳ module nào dùng app.core.database
from mongomock_motor import AsyncMongoMockClient
import app.core.database as db_module

mock_client = AsyncMongoMockClient()
mock_db = mock_client["knowledge_hub_test"]
db_module.db = mock_db
db_module.users_col = mock_db["users"]
db_module.questions_col = mock_db["questions"]
db_module.answers_col = mock_db["answers"]
db_module.comments_col = mock_db["comments"]
db_module.votes_col = mock_db["votes"]
db_module.tags_col = mock_db["tags"]
db_module.question_vectors_tfidf_col = mock_db["question_vectors_tfidf"]
db_module.question_vectors_sbert_col = mock_db["question_vectors_sbert"]
db_module.tfidf_vocabulary_col = mock_db["tfidf_vocabulary"]
db_module.search_benchmark_log_col = mock_db["search_benchmark_log"]

# Patch lại reference trong các module đã import db trực tiếp
import app.routers.auth as auth_router
import app.routers.questions as questions_router
import app.routers.answers as answers_router
import app.routers.comments as comments_router
import app.routers.tags as tags_router
import app.routers.admin as admin_router
import app.routers.votes as votes_router
import app.routers.search as search_router
import app.services.reputation_service as reputation_service
import app.services.tag_service as tag_service
import app.services.search.tfidf_service as tfidf_service
import app.services.search.sbert_service as sbert_service
import app.core.security as security_module

auth_router.users_col = mock_db["users"]
questions_router.questions_col = mock_db["questions"]
questions_router.answers_col = mock_db["answers"]
questions_router.comments_col = mock_db["comments"]
questions_router.votes_col = mock_db["votes"]
answers_router.answers_col = mock_db["answers"]
answers_router.questions_col = mock_db["questions"]
answers_router.comments_col = mock_db["comments"]
answers_router.votes_col = mock_db["votes"]
comments_router.comments_col = mock_db["comments"]
comments_router.questions_col = mock_db["questions"]
comments_router.answers_col = mock_db["answers"]
comments_router.COLLECTION_BY_TYPE = {"question": mock_db["questions"], "answer": mock_db["answers"]}
tags_router.tags_col = mock_db["tags"]
admin_router.users_col = mock_db["users"]
votes_router.votes_col = mock_db["votes"]
votes_router.questions_col = mock_db["questions"]
votes_router.answers_col = mock_db["answers"]
votes_router.COLLECTION_BY_TYPE = {"question": mock_db["questions"], "answer": mock_db["answers"]}
search_router.questions_col = mock_db["questions"]
search_router.search_benchmark_log_col = mock_db["search_benchmark_log"]
reputation_service.users_col = mock_db["users"]
tag_service.tags_col = mock_db["tags"]
tfidf_service.questions_col = mock_db["questions"]
tfidf_service.question_vectors_tfidf_col = mock_db["question_vectors_tfidf"]
tfidf_service.tfidf_vocabulary_col = mock_db["tfidf_vocabulary"]
sbert_service.questions_col = mock_db["questions"]
sbert_service.question_vectors_sbert_col = mock_db["question_vectors_sbert"]
security_module.users_col = mock_db["users"]

from fastapi.testclient import TestClient
from app.main import app as fastapi_app


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        raise SystemExit(f"Test thất bại tại: {label}")


async def run():
    with TestClient(fastapi_app) as client:
        # --- 1. Đăng ký 2 user: newbie (rep=1 mặc định) và seed thủ công critic (rep=130) ---
        r = client.post("/api/auth/register", json={
            "username": "newbie_test", "email": "newbie_test@example.com", "password": "Test@123"
        })
        check("Đăng ký newbie_test thành công (201)", r.status_code == 201)
        newbie_token = r.json()["token"]
        check("Reputation mặc định = 1", r.json()["user"]["reputation"] == 1)

        r = client.post("/api/auth/register", json={
            "username": "author_test", "email": "author_test@example.com", "password": "Test@123"
        })
        check("Đăng ký author_test thành công (201)", r.status_code == 201)
        author_token = r.json()["token"]
        author_id = r.json()["user"]["id"]

        # Bơm thẳng reputation=130 cho 1 user để test downvote (giả lập kết quả seed.py)
        await db_module.users_col.update_one({"username": "newbie_test"}, {"$set": {"reputation": 130}})
        r = client.post("/api/auth/login", json={"username": "newbie_test", "password": "Test@123"})
        critic_token = r.json()["token"]
        check("Login lại lấy token mới có reputation=130", r.json()["user"]["reputation"] == 130)

        # --- 2. author_test tạo câu hỏi ---
        r = client.post("/api/questions",
                         headers={"Authorization": f"Bearer {author_token}"},
                         json={"title": "Cosine similarity dùng để làm gì trong tìm kiếm?",
                               "body": "Giải thích chi tiết...", "tags": ["nlp", "search"]})
        check("Tạo câu hỏi thành công (201)", r.status_code == 201)
        question = r.json()["question"]
        check("isIndexed mặc định = False", question["isIndexed"] is False)
        question_id = question["id"]

        # --- 3. newbie (rep=1, dùng token cũ trước khi bơm rep) thử downvote -> phải bị từ chối 403 ---
        r = client.post("/api/auth/register", json={
            "username": "poor_test", "email": "poor_test@example.com", "password": "Test@123"
        })
        poor_token = r.json()["token"]
        r = client.post("/api/votes",
                         headers={"Authorization": f"Bearer {poor_token}"},
                         json={"targetType": "question", "targetId": question_id, "value": -1})
        check("User rep=1 downvote bị từ chối (403)", r.status_code == 403)
        check("Thông báo đúng ngưỡng 125", "125" in str(r.json()["detail"]))

        # --- 4. user rep=130 (critic_token) downvote -> phải thành công ---
        r = client.post("/api/votes",
                         headers={"Authorization": f"Bearer {critic_token}"},
                         json={"targetType": "question", "targetId": question_id, "value": -1})
        check("User rep=130 downvote thành công (201)", r.status_code == 201)
        check("voteScore câu hỏi giảm còn -1", r.json()["newVoteScore"] == -1)

        # --- 5. Kiểm tra reputation: author giảm 2, critic giảm 1 (chi phí downvote) ---
        author_doc = await db_module.users_col.find_one({"username": "author_test"})
        check("Reputation tác giả giảm 2 điểm (1 -> -1 -> chặn về 1)",
              author_doc["reputation"] == 1)  # 1 - 2 = -1, nhưng service chặn floor tại 1

        critic_doc = await db_module.users_col.find_one({"username": "newbie_test"})
        check("Reputation người downvote giảm 1 điểm (130 -> 129)", critic_doc["reputation"] == 129)

        # --- 6. Vote trùng lần 2 -> phải bị từ chối 409 ---
        r = client.post("/api/votes",
                         headers={"Authorization": f"Bearer {critic_token}"},
                         json={"targetType": "question", "targetId": question_id, "value": -1})
        check("Vote trùng lần 2 bị từ chối (409)", r.status_code == 409)

        # --- 7. newbie thử sửa câu hỏi của author (không phải chủ, rep thấp) -> 403 ---
        r = client.put(f"/api/questions/{question_id}",
                        headers={"Authorization": f"Bearer {poor_token}"},
                        json={"title": "Sửa trộm tiêu đề"})
        check("User không đủ quyền sửa bài người khác bị từ chối (403)", r.status_code == 403)

        # --- 8. author tự sửa câu hỏi của mình -> phải thành công, isIndexed reset về False ---
        r = client.put(f"/api/questions/{question_id}",
                        headers={"Authorization": f"Bearer {author_token}"},
                        json={"title": "Cosine similarity là gì? (đã sửa)"})
        check("Chủ sở hữu tự sửa câu hỏi thành công (200)", r.status_code == 200)
        check("isIndexed reset về False sau khi đổi title", r.json()["question"]["isIndexed"] is False)

        # --- 9. answers: poor_test (rep=1) trả lời câu hỏi -> phải thành công (ASK_ANSWER chỉ cần rep=1) ---
        r = client.post(f"/api/questions/{question_id}/answers",
                         headers={"Authorization": f"Bearer {poor_token}"},
                         json={"body": "Cosine similarity đo góc giữa 2 vector..."})
        check("poor_test (rep=1) trả lời câu hỏi thành công (201)", r.status_code == 201)
        answer = r.json()["answer"]
        answer_id = answer["id"]
        check("isAccepted mặc định = False", answer["isAccepted"] is False)

        r = client.get(f"/api/questions/{question_id}/answers")
        check("List answers trả về 1 câu trả lời", len(r.json()["answers"]) == 1)

        q_after = client.get(f"/api/questions/{question_id}").json()["question"]
        check("answerCount câu hỏi tăng lên 1", q_after["answerCount"] == 1)

        # --- 10. author (chủ câu hỏi) accept câu trả lời -> answer author (+15 rep) ---
        r = client.post(f"/api/answers/{answer_id}/accept", headers={"Authorization": f"Bearer {author_token}"})
        check("Author accept answer thành công (200)", r.status_code == 200)
        check("isAccepted = True sau khi accept", r.json()["answer"]["isAccepted"] is True)

        poor_doc = await db_module.users_col.find_one({"username": "poor_test"})
        check("Reputation người trả lời +15 sau khi được accept (1 -> 16)", poor_doc["reputation"] == 16)

        # người không phải chủ câu hỏi thử accept -> 403
        r = client.post(f"/api/answers/{answer_id}/accept", headers={"Authorization": f"Bearer {poor_token}"})
        check("User không phải chủ câu hỏi accept bị từ chối (403)", r.status_code == 403)

        # --- 11. comments: poor_test (rep=16 < 50) bình luận bài CỦA CHÍNH MÌNH -> OK ---
        r = client.post("/api/comments", headers={"Authorization": f"Bearer {poor_token}"},
                         json={"targetType": "answer", "targetId": answer_id, "content": "Bổ sung: cosine trong [-1,1]"})
        check("Rep thấp bình luận bài của CHÍNH MÌNH thành công (201)", r.status_code == 201)
        comment_id = r.json()["comment"]["id"]

        # poor_test (rep=16 < 50) bình luận bài của NGƯỜI KHÁC (câu hỏi của author) -> 403
        r = client.post("/api/comments", headers={"Authorization": f"Bearer {poor_token}"},
                         json={"targetType": "question", "targetId": question_id, "content": "Câu hỏi hay!"})
        check("Rep thấp (<50) bình luận bài NGƯỜI KHÁC bị từ chối (403)", r.status_code == 403)

        # critic (rep=129 >= 50) bình luận bài người khác -> OK
        r = client.post("/api/comments", headers={"Authorization": f"Bearer {critic_token}"},
                         json={"targetType": "question", "targetId": question_id, "content": "Câu hỏi hay!"})
        check("Rep>=50 bình luận bài người khác thành công (201)", r.status_code == 201)

        r = client.get(f"/api/comments?targetType=answer&targetId={answer_id}")
        check("List comments của answer trả về 1 bình luận", len(r.json()["comments"]) == 1)

        r = client.delete(f"/api/comments/{comment_id}", headers={"Authorization": f"Bearer {poor_token}"})
        check("Chủ bình luận tự xóa được comment (200)", r.status_code == 200)

        # --- 12. tags: tag được tự tạo "hữu cơ" khi đăng câu hỏi (nlp, search) ---
        r = client.get("/api/tags")
        tag_names = {t["name"] for t in r.json()["tags"]}
        check("Tag 'nlp' và 'search' tự sinh khi tạo câu hỏi", {"nlp", "search"}.issubset(tag_names))

        r = client.post("/api/tags", headers={"Authorization": f"Bearer {poor_token}"},
                         json={"name": "hacker-tag", "description": "..."})
        check("User thường tạo tag bị từ chối (403)", r.status_code == 403)

        # --- 13. admin: cần tài khoản isAdmin=true - bơm tay như seed.py làm ---
        await db_module.users_col.update_one({"username": "author_test"}, {"$set": {"isAdmin": True}})
        r = client.post("/api/auth/login", json={"username": "author_test", "password": "Test@123"})
        admin_token = r.json()["token"]

        r = client.post("/api/tags", headers={"Authorization": f"Bearer {admin_token}"},
                         json={"name": "admin-tag", "description": "Tag do admin tạo"})
        check("Admin tạo tag thành công (201)", r.status_code == 201)

        r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
        check("Admin xem danh sách user thành công (200)", r.status_code == 200)
        check("Danh sách user không rỗng", len(r.json()["users"]) >= 3)

        r = client.get("/api/admin/users", headers={"Authorization": f"Bearer {poor_token}"})
        check("User thường xem /api/admin/users bị từ chối (403)", r.status_code == 403)

        r = client.patch(f"/api/admin/users/{author_id}/ban", headers={"Authorization": f"Bearer {admin_token}"},
                          json={"isBanned": True})
        check("Admin ban user thành công (200)", r.status_code == 200)
        r = client.post("/api/auth/login", json={"username": "author_test", "password": "Test@123"})
        check("User bị ban không login được (403)", r.status_code == 403)
        # Un-ban lại để không ảnh hưởng phần test search phía dưới (author_test cần đăng thêm câu hỏi)
        await db_module.users_col.update_one({"username": "author_test"}, {"$set": {"isBanned": False}})

        # --- 14. delete_question cascade: xóa câu hỏi phải dọn theo answer/comment/vote ---
        r = client.post("/api/questions", headers={"Authorization": f"Bearer {admin_token}"},
                         json={"title": "Câu hỏi tạm để test cascade delete", "body": "...", "tags": ["temp"]})
        temp_qid = r.json()["question"]["id"]
        client.post(f"/api/questions/{temp_qid}/answers", headers={"Authorization": f"Bearer {poor_token}"},
                    json={"body": "Trả lời tạm"})
        r = client.delete(f"/api/questions/{temp_qid}", headers={"Authorization": f"Bearer {admin_token}"})
        check("Admin xóa câu hỏi (cascade) thành công (200)", r.status_code == 200)
        remaining_answers = await db_module.answers_col.count_documents({})
        check("Answer của câu hỏi đã xóa cũng bị dọn theo (cascade)",
              remaining_answers == 1)  # chỉ còn lại answer của question_id ban đầu

        # --- 15. TF-IDF search: reindex thủ công (admin) rồi tìm bằng từ khóa liên quan ---
        r = client.post("/api/admin/search/reindex", headers={"Authorization": f"Bearer {admin_token}"})
        check("Admin trigger reindex thành công (200)", r.status_code == 200)
        check("TF-IDF đã index >=1 câu hỏi", r.json()["tfidf"]["indexed"] >= 1)

        r = client.get("/api/search/tfidf", params={"q": "cosine similarity tìm kiếm"})
        check("Search TF-IDF trả về 200", r.status_code == 200)
        check("Search TF-IDF trả về ít nhất 1 kết quả liên quan",
              any("cosine" in item["title"].lower() for item in r.json()["results"]))

        r = client.get("/api/admin/search/benchmark-log", headers={"Authorization": f"Bearer {admin_token}"})
        check("Admin xem benchmark log thành công (200)", r.status_code == 200)
        check("Benchmark log có ghi nhận ít nhất 1 lượt search", len(r.json()["logs"]) >= 1)

        print("\n✅ TẤT CẢ TEST END-TO-END ĐỀU PASS — logic reputation-gated hoạt động đúng thiết kế.")


if __name__ == "__main__":
    asyncio.run(run())
