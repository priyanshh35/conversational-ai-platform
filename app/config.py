from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_KEY: str

    CHAT_BASE_URL: str
    EMBED_BASE_URL: str
    RERANK_BASE_URL: str

    MODEL_NAME: str = "usf1-mini"
    EMBEDDING_MODEL: str = "usf-embed"
    RERANK_MODEL: str = "usf-rerank"

    DATABASE_URL: str = "sqlite:///./conversations.db"
    CHROMA_DB_PATH: str = "./chroma_db"
    MAX_HISTORY_TURNS: int = 10

    class Config:
        env_file = ".env"


settings = Settings()