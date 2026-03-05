import base64
import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing import Any, Dict, List

from config import settings

logger = logging.getLogger(__name__)

base_llm = ChatOpenAI(
    model=settings.VISION_MODEL,
    api_key=settings.OPENAI_API_KEY
)

llm_json = base_llm.bind(
    response_format={"type": "json_object"}
)

VISION_ANALYSIS_PROMPT_RU = """
Проанализируй документ. Извлеки текст, структуру, ключевые факты, коды ошибок.
Верни строго валидный JSON в следующем формате (без пояснений, только JSON):
{
  "summary": "краткое содержание документа на русском языке",
  "key_points": ["ключевой пункт 1", "ключевой пункт 2"],
  "errors": ["error 1", "error 2"],
  "recommendations": ["рекомендация 1", "рекомендация 2"]
}
""".strip()

def _safe_parse_analysis_json(raw_text: str) -> Dict[str, Any]:
    """
    Пытается распарсить вывод модели как JSON и обеспечить наличие обязательных ключей.
    Если парсинг не удался, оборачивает исходный текст в структуру по умолчанию.
    """
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.warning("JSON decode error: %s; raw=%r", e, raw_text[:500])
        data = {"summary": raw_text}

    if not isinstance(data, dict):
        data = {"summary": str(data)}

    summary = data.get("summary") or ""
    key_points = data.get("key_points") or []
    errors = data.get("errors") or []
    recommendations = data.get("recommendations") or []

    if not isinstance(key_points, list):
        key_points = [key_points]
    if not isinstance(errors, list):
        errors = [errors]
    if not isinstance(recommendations, list):
        recommendations = [recommendations]

    return {
        "summary": str(summary),
        "key_points": [str(v) for v in key_points],
        "errors": [str(v) for v in errors],
        "recommendations": [str(v) for v in recommendations],
    }

async def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Анализирует изображение документа с помощью GPT с возможностями зрения.
    """
    logger.info("Начало анализа изображения документа (Vision)")
    
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    image_url = f"data:image/png;base64,{b64_image}"

    msg = HumanMessage(
        content=[
            {"type": "text", "text": VISION_ANALYSIS_PROMPT_RU},
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                },
            },
        ]
    )

    resp = await llm_json.ainvoke([msg])
    raw_text = resp.content or ""

    logger.info("Проанализировали изображение: %s", raw_text)

    result = _safe_parse_analysis_json(raw_text)
    return result
