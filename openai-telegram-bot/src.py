import os  # Импортируем стандартный модуль для работы с операционной системой и переменными окружения
from dotenv import load_dotenv  # Импортируем функцию для загрузки переменных окружения из файла .env

load_dotenv()  # Загружаем переменные окружения из файла .env в текущую рабочую среду

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
