import mimetypes
import base64
import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from settings import *

SYSTEM_PROMPT = """
Ты ассистент по распознаванию и анализу документов.
Твои задачи:
1) Аккуратно считывать текст с рукописных и печатных документов.
2) Пытаться понять структуру документа и извлечь из него основные данные.
3) Возвращать результат строго в формате JSON.

Под "основными данными" подразумеваются:
- реквизиты (имена, фамилии, номера телефонов, email, адреса);
- даты, суммы, валюты;
- заголовок документа, номер документа;
- табличные данные (списки позиций, строк таблицы и т.п.);
- любые явно важные значения, встречающиеся в документе.

Структура итогового JSON (примерная, можно не использовать все поля, если данных нет):
{
  "document_type": "...",        // тип документа, если удаётся понять (например: "заявление", "квитанция", "анкета", "заметка")
  "title": "...",                // заголовок, если есть
  "people": [
    {
      "full_name": "...",
      "role": "...",             // например: "отправитель", "получатель", "подписант"
      "contacts": {
        "phone": "...",
        "email": "...",
        "address": "..."
      }
    }
  ],
  "dates": [
    {
      "label": "...",            // например: "дата составления", "дата рождения"
      "value": "YYYY-MM-DD"      // по возможности нормализуй; если не получается, оставь исходный формат
    }
  ],
  "amounts": [
    {
      "label": "...",
      "value": number,
      "currency": "..."
    }
  ],
  "fields": {                    // произвольные ключ-значение пары по документу
    "ключ": "значение"
  },
  "tables": [
    {
      "name": "...",             // название таблицы, если есть
      "columns": ["...", "..."],
      "rows": [
        ["значение1", "значение2"],
        ["...", "..."]
      ]
    }
  ],
  "raw_text": "полный распознанный текст документа одной строкой"
}

В ответе НЕЛЬЗЯ добавлять никакие пояснения вне JSON.
НЕ пиши текст до или после JSON.
"""

def encode_image_to_data_url(image_path: str) -> str:
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Файл не найден: {image_path}")

    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{b64}"

def extract_document(image_path: str, model: str = "gpt-4o"):
    print(f'Processing document {image_path}, model: {model}')

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Не задан OPENAI_API_KEY в переменных окружения.")
    
    llm = ChatOpenAI(
        model=model,
        temperature=0.1,
        api_key=api_key,
    ).bind(
        # Включаем JSON‑mode (аналог response_format={"type": "json_object"})
        response_format={"type": "json_object"}
    )

    image_data_url = encode_image_to_data_url(image_path)

    system = SystemMessage(content=SYSTEM_PROMPT)
    user = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Проанализируй этот рукописный/печатный документ на изображении "
                    "и верни только JSON по описанной в system-подсказке схеме."
                ),
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_url,
                },
            },
        ]
    )

    response = llm.invoke([system, user])

    content = response.content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Не удалось распарсить ответ модели как JSON: {e}\nОтвет:\n{content}"
        )
    
    return data
