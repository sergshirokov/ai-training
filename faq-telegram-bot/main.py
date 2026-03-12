import asyncio
import logging

from config import Config
from qa_processor import QaProcessor
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Снижаем шум от библиотеки telegram
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    logger.info("Команда /start от user_id=%s", update.effective_user.id if update.effective_user else None)
    await update.message.reply_text(
        "Привет! Я AI-ассистент по программированию на Python. Задайте вопрос по Python — синтаксису, библиотекам, фреймворкам, лучшим практикам — постараюсь ответить."
    )


async def _keep_typing(chat, interval: float = 4.0) -> None:
    """Периодически отправляет «печатает», т.к. в Telegram индикатор живёт ~5 с."""
    while True:
        await chat.send_chat_action("typing")
        await asyncio.sleep(interval)


ERROR_MESSAGE = (
    "Произошла ошибка при формировании ответа. Попробуйте повторить запрос позже."
)


async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает на вопрос пользователя через GigaChat."""
    try:
        qa: QaProcessor = context.application.bot_data["qa_processor"]
        question = update.message.text or ""
        logger.info(
            "Вопрос от user_id=%s: %s",
            update.effective_user.id if update.effective_user else None,
            question[:100],
        )
        typing_task = asyncio.create_task(_keep_typing(update.effective_chat))
        try:
            answer_text = await asyncio.to_thread(qa.answer, question)
        finally:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
        if len(answer_text) > 4096:
            answer_text = answer_text[:4093] + "..."
        await update.message.reply_text(answer_text)
    except Exception:
        logger.exception("Ошибка при обработке вопроса")
        await update.message.reply_text(ERROR_MESSAGE)


def main() -> None:
    config = Config()
    token = config.bot_token
    qa_processor = QaProcessor(
        credentials=config.gigachat_credentials,
        verify_ssl_certs=False,
    )

    # Таймауты 20 с для медленного интернета
    request = HTTPXRequest(
        connect_timeout=20,
        read_timeout=20,
        write_timeout=20,
        pool_timeout=20,
        media_write_timeout=20,
    )
    app = (
        Application.builder()
        .token(token)
        .request(request)
        .get_updates_request(request)
        .build()
    )
    app.bot_data["qa_processor"] = qa_processor

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question))

    logger.info("Бот запущен (polling)")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
