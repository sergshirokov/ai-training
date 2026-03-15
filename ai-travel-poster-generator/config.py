import os
from dotenv import load_dotenv


class Config:
    def __init__(self, env_path: str = ".env"):
        load_dotenv(env_path)

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. "
                "Create a .env file with OPENAI_API_KEY=sk-..."
            )

        self.gigachat_api_key = os.getenv("GIGACHAT_API_KEY")
        if not self.gigachat_api_key:
            raise ValueError(
                "GIGACHAT_API_KEY is not set. "
                "Create a .env file with GIGACHAT_API_KEY=..."
            )
