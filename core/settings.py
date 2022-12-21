from typing import List

from pydantic import BaseSettings, PostgresDsn, validator


class PostgresConfig(BaseSettings):
    DB: str
    USER: str
    PASS: str
    HOST: str
    PORT: int
    URL: str = None

    @validator('URL', pre=True)
    def url(cls, _, values):
        return PostgresDsn.build(
            scheme='postgresql+asyncpg',
            user=values.get('USER'),
            password=values.get('PASS'),
            host=values.get('HOST'),
            port=str(values.get('PORT')),
            path=f"/{values.get('DB') or ''}",
        )

    class Config:
        env_prefix = 'PG_'
        env_file = '.env'


class Settings(BaseSettings):
    LOGGING_LEVEL: str = 'DEBUG'

    API_TOKEN: str
    ACCESS_IDS: List[str]

    DIFFERENCE_WITH_UTC: int

    CURRENCY: str

    POSTGRES_CONFIG: PostgresConfig = PostgresConfig()

    class Config:
        env_file = ".env"


settings = Settings()
