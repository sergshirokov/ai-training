import logging

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from telegram.error import TimedOut

from config import settings
from speech_handler.stt import transcribe_audio
from image_handler.image_processor import analyze_image

from assistant_logic.processor import process_support_request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

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
    logger.info("handle_start user_id=%s", update.effective_user.id)

    await send_with_retry(update, 
        "👋 Привет! Я бот-помощник обращений в службу поддержки клиентов.\n"
        "Задай свой вопрос текстом или голосом, если есть скрин ошибки, присылай."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("handle_text user_id=%s", update.effective_user.id)

    status_msg = await send_with_retry(update, "⏳ Обрабатываю запрос...")
    user_message = update.message.text

    try:
        response_text = await process_support_request(user_message)
        await update_with_retry(status_msg, response_text)
    except Exception as e:
        logger.error(e)
        await send_with_retry(update, "Ошибка при обработке запроса. Попробуйте позже.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("handle_photo user_id=%s", update.effective_user.id)

    status_msg = await send_with_retry(update, "⏳ Обрабатываю запрос...")

    user_message = update.message.caption
    photo = update.message.photo[-1]

    file_info = await context.bot.get_file(photo.file_id)
    user_photo = await file_info.download_as_bytearray()

    image_info = await analyze_image(user_photo)

    try:
        response_text = await process_support_request(user_message, image_info)
        await update_with_retry(status_msg, response_text)
    except Exception as e:
        logger.error(e)
        await send_with_retry(update, "Ошибка при обработке запроса. Попробуйте позже.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("handle_voice user_id=%s", update.effective_user.id)

    status_msg = await send_with_retry(update, "⏳ Обрабатываю запрос...")

    voice = update.message.voice

    file_info = await context.bot.get_file(voice.file_id)
    user_voice = await file_info.download_as_bytearray()

    user_message = await transcribe_audio(user_voice)

    try:
        response_text = await process_support_request(user_message)
        await update_with_retry(status_msg, response_text)
    except Exception as e:
        logger.error(e)
        await send_with_retry(update, "Ошибка при обработке запроса. Попробуйте позже.")

def main():
    app = ApplicationBuilder() \
        .token(settings.BOT_TOKEN) \
        .read_timeout(20) \
        .write_timeout(20) \
        .connect_timeout(20) \
        .pool_timeout(20) \
        .build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_photo))
    app.add_handler(MessageHandler(filters.VOICE & ~filters.COMMAND, handle_voice))

    logger.info("✅ Bot started!")

    app.run_polling()

if __name__ == "__main__":
    main()
