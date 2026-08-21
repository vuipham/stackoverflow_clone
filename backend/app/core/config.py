from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "knowledge_hub"
    jwt_secret: str = "change-me"
    jwt_expires_minutes: int = 10080  # 7 ngày
    port: int = 8000

    # Tuần 2 - Chức năng B: model SBERT pretrained (không tự train, theo đúng lưu ý Phần 6)
    # multilingual vì dataset tiêu đề có thể trộn tiếng Việt + thuật ngữ tiếng Anh.
    sbert_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    search_top_k_default: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
