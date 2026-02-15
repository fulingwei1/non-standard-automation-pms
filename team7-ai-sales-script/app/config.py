from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/presale_db"
    OPENAI_API_KEY: Optional[str] = None
    KIMI_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "openai"  # or "kimi"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
