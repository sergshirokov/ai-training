import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from typing import Any, Dict, List

from config import settings

logger = logging.getLogger(__name__)

base_llm = ChatOpenAI(
    model=settings.ANALYSE_MODEL,
    api_key=settings.OPENAI_API_KEY
)

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["user_message", "additional_info"],
    template="""
Ты опытный специалист технической поддержки, проанализируй вопрос пользователя,
дополнительную информацию, которую он прислал и сформулируй ответ.

Вопрос пользователя:
''''
{user_message}
''''

Дополнительная информация:
....
{additional_info}
....

Ответ дай кратко, факты не придумывай, если не знаешь или мало данных, так и ответь.
"""
)

async def process_support_request(user_message: str, analysis: Dict[str, Any] = None) -> str:
    logger.info("Начало обработки ответа user_message: %s", user_message);

    chain = SYSTEM_PROMPT | base_llm

    if analysis:
        additional_info = format_analysis_report(analysis)
    else:
        additional_info = ""

    logger.info("additional_info: %s", additional_info);

    response = await chain.ainvoke({"user_message": user_message, "additional_info": additional_info})

    return response.text

def format_analysis_report(analysis: Dict[str, Any]) -> str:
    """
    Преобразует структурированный JSON анализа в читаемый текстовый отчёт.
    """
    summary = analysis.get("summary") or "Нет краткого резюме."
    key_points = analysis.get("key_points") or []
    errors = analysis.get("errors") or []
    recommendations = analysis.get("recommendations") or []

    lines: list[str] = []
    lines.append("📄 Итоговый отчёт по документу\n")
    lines.append("📝 Краткое резюме:")
    lines.append(summary)

    if key_points:
        lines.append("\n🔑 Ключевые пункты:")
        for idx, point in enumerate(key_points, start=1):
            lines.append(f"{idx}. {point}")

    if errors:
        lines.append("\n⚠️ Ошибки:")
        for idx, error in enumerate(errors, start=1):
            lines.append(f"{idx}. {error}")

    if recommendations:
        lines.append("\n✅ Рекомендации:")
        for idx, rec in enumerate(recommendations, start=1):
            lines.append(f"{idx}. {rec}")

    return "\n".join(lines)