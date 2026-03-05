from dataclasses import dataclass
import os
from dotenv import load_dotenv

@dataclass
class Settings:
    OPENAI_API_KEY: str
    BOT_TOKEN: str
    STT_MODEL: str
    VISION_MODEL: str
    ANALYSE_MODEL: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise SystemExit("Не найден OPENAI_API_KEY. Укажите его в .env или переменных окружения.")

        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise SystemExit("Не найден BOT_TOKEN. Укажите его в .env или переменных окружения.")
        
        stt_model = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
        vision_model = os.getenv("VISION_MODEL", "gpt-4o")
        analyze_model = os.getenv("ANALYSE_MODEL", "gpt-4o")

        return cls(
                OPENAI_API_KEY=openai_api_key,
                BOT_TOKEN=bot_token,
                STT_MODEL=stt_model,
                VISION_MODEL=vision_model,
                ANALYSE_MODEL=analyze_model,
        )

settings = Settings.from_env()