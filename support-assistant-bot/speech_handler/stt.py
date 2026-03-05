import logging

from io import BytesIO
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key = settings.OPENAI_API_KEY
)

async def transcribe_audio(audio_bytes: bytes) -> str:
    logger.info("Запрос STT: размер аудио=%d байт", len(audio_bytes))

    buffer = BytesIO(audio_bytes)
    buffer.name = "audio.ogg"

    transcription = await client.audio.transcriptions.create(
        model=settings.STT_MODEL,
        file=buffer,
        response_format="text",
    )

    if isinstance(transcription, str):
        logger.info("Ответ STT (строка), длина=%d", len(transcription))
        return transcription

    text = getattr(transcription, "text", "")
    logger.info("Ответ STT (объект), длина=%d", len(text))
    return text
