import logging
import asyncio

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import TimedOut

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langfuse import Langfuse
from langfuse import observe, get_client
from langfuse.langchain import CallbackHandler

from src import *  # Импорт всех настроек, включая токены и ключи, из локального файла настроек
from prompts import main_prompt

logging.basicConfig(level=logging.INFO)  # Устанавливаем базовый уровень логирования — INFO
logger = logging.getLogger(__name__)  # Получаем объект логгера для текущего модуля

langfuse_client = Langfuse(
    secret_key = LANGFUSE_SECRET_KEY,
    public_key = LANGFUSE_PUBLIC_KEY,
    host="https://cloud.langfuse.com"
)

async def send_with_retry(update, text, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return await update.message.reply_text(text)
        except TimedOut:
            if attempt == max_retries - 1:
                raise  # последняя попытка — пробрасываем ошибку
            await asyncio.sleep(delay * (2 ** attempt))  # экспоненциальная задержка
    raise TimedOut("All retry attempts failed")

async def update_with_retry(status_message, text, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return await status_message.edit_text(text)
        except TimedOut:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (2 ** attempt))
    raise TimedOut("All retry attempts failed")

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_with_retry(update, 
        "👋 Привет! Я бот-помощник через OpenAI Langchain API.\n"
        "Задай вопрос что отделываем в квартире и я подберу отделочный материал."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text  # Получаем текст сообщения пользователя
    status_msg = await send_with_retry(update, "⏳ Обрабатываю запрос...")  # Отправляем пользователю статус о начале обработки

    try:
        response_text = get_bot_ai_response(user_message)
        await update_with_retry(status_msg, response_text)  # Обновляем статусное сообщение реальным ответом от модели
    except Exception as e:
        logger.error(e)
        await send_with_retry(update, "Ошибка при обработке запроса. Попробуйте позже.")

langfuse_handler = CallbackHandler()

@observe
def get_bot_ai_response(user_input: str) -> str:
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key = OPENAI_API_KEY)

    chain = main_prompt | llm

    response = chain.invoke({"user_input": user_input}, config={"callbacks": [langfuse_handler]})

    return response.content

def main():
    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .read_timeout(10) \
        .write_timeout(10) \
        .connect_timeout(10) \
        .pool_timeout(10) \
        .build()

    # Добавляем обработчики команд и сообщений
    app.add_handler(CommandHandler("start", handle_start))  
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  

    print("✅ Bot started!")

    app.run_polling()  # Запускаем бесконечный цикл ожидания событий (polling)

# --- Точка входа ---
if __name__ == "__main__":
    main()  # Запускаем основную функцию при запуске скрипта напрямую
