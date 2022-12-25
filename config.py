from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_INITDB_DATABASE: str

    FROM_ADDR: str
    EMAIL_PWD: str

    SMTP: str
    SMTP_PORT: str

    class Config:
        env_file = "./.env"


settings = Settings()
