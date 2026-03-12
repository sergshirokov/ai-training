"""AI-ассистент на базе GigaChat для ответов на вопросы по Python."""

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — ассистент-эксперт по программированию на Python. Твоя задача — отвечать только на вопросы, связанные с Python: синтаксис, стандартная библиотека, типизация, лучшие практики, популярные фреймворки (Django, FastAPI и т.д.), виртуальные окружения, инструменты разработки.

Если вопрос не относится к Python или программированию вообще — вежливо откажись и предложи задать вопрос по Python. Отвечай кратко и по делу, на русском языке."""


class QaProcessor:
    """Ассистент по Python: отвечает только на вопросы о программировании на Python."""

    model: str = "GigaChat-2-Max"
    temperature: float = 0.1

    def __init__(self, credentials: str, verify_ssl_certs: bool = False) -> None:
        self._llm = GigaChat(
            credentials=credentials,
            verify_ssl_certs=verify_ssl_certs,
            model=self.model,
            temperature=self.temperature,
        )

    def answer(self, question: str) -> str:
        """Синхронный ответ на вопрос (с системным промптом про Python)."""
        if not question or not question.strip():
            return "Задайте, пожалуйста, текст вопроса."
        try:
            # Раскомментировать для проверки обработки ошибок (ответ в чат + лог):
            # raise RuntimeError("Эмуляция ошибки для теста")
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=question.strip()),
            ]
            response = self._llm.invoke(messages)
            text = response.content if hasattr(response, "content") else str(response)
            return text or "Не удалось получить ответ."
        except Exception as e:
            logger.exception("Ошибка GigaChat: %s", e)
            return (
                "Произошла ошибка при формировании ответа. "
                "Попробуйте повторить запрос позже."
            )
