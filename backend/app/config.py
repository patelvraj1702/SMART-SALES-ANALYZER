"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "smart_sales_analyzer"

    # JWT
    JWT_SECRET: str = "change-me-in-production-use-32-chars-min"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Spark
    SPARK_HOME: str = r"C:\spark"
    SPARK_SUBMIT: str = r"C:\spark\bin\spark-submit.cmd"
    SPARK_JAR: str = r"spark-engine\target\scala-2.12\smart-sales-analyzer-spark-assembly-1.0.0.jar"
    SPARK_TIMEOUT_SECONDS: int = 300

    # Upload limits
    MAX_FILE_SIZE_MB: int = 50
    MAX_ROWS: int = 500_000

    # Temp directory for Spark job files
    TEMP_DIR: str = "temp_jobs"


settings = Settings()
