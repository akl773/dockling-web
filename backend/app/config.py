from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", case_sensitive=False
    )

    app_title: str = "Docling Web"
    database_url: str = "sqlite:////data/app.db"
    data_dir: Path = Path("/data")
    frontend_dist_dir: Path = Path("/app/frontend-dist")
    worker_poll_interval: float = 1.0
    max_concurrent_jobs: int = 1
    omp_num_threads: int = 4
