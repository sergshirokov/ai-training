import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Загрузка конфигурации из .env файла."""

    _env_loaded = False

    def __init__(self, env_path: str | Path | None = None) -> None:
        if env_path is None:
            env_path = Path(__file__).resolve().parent / ".env"
        if not Config._env_loaded:
            load_dotenv(env_path)
            Config._env_loaded = True
        self._token = os.environ.get("BOT_TOKEN", "").strip()
        self._gigachat_credentials = os.environ.get("GIGACHAT_CREDENTIALS", "").strip()

    @property
    def bot_token(self) -> str:
        if not self._token:
            raise ValueError("BOT_TOKEN не задан в .env")
        return self._token

    @property
    def gigachat_credentials(self) -> str:
        if not self._gigachat_credentials:
            raise ValueError("GIGACHAT_CREDENTIALS не задан в .env")
        return self._gigachat_credentials
