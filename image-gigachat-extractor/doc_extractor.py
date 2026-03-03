import json

from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage

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

def extract_document(image_path: str, model: str):
    print(f'Processing document {image_path}, model: {model}')

    api_key = os.getenv("GIGACHAT_API_KEY")
    if not api_key:
        raise RuntimeError("Не задан GIGACHAT_API_KEY в переменных окружения.")
    
    giga = GigaChat(
        model=model,         # Используемая модель. "GigaChat-2-Max" — название LLM модели GigaChat.
        credentials=api_key,                 # Ваш токен авторизации или ключ доступа к GigaChat API (пусто — заменить своим).
        scope='GIGACHAT_API_PERS',      # Область действия токена (например, персональный API).
        temperature=0.1,
        verify_ssl_certs=False,         # Отключение проверки SSL-сертификатов (используется для тестов или некорректных сертификатов).
        profanity_check=True            # Включение проверки и фильтрации нецензурной лексики в ответах модели.
    )

    with open(image_path, "rb") as f:
        file_obj = giga.upload_file(f)

    if not file_obj:
        raise RuntimeError(f"Не удалось загрузить файл")
    
    try:
      messages = [
          ("system", SYSTEM_PROMPT),
          HumanMessage(
              content=(
                  "На изображении находится рукописный или печатный документ. "
                  "Проанализируй его и верни только JSON по описанной в system-подсказке схеме."
              ),
              additional_kwargs={"attachments": [file_obj.id_]},
          ),
      ]

      response = giga.invoke(messages)

    finally:
        print("Загруженный файл:" + file_obj.id_)
#      giga.delete_file(file_obj.id_) не находит такого атрибута
        
    content = response.content.strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Не удалось распарсить ответ модели как JSON: {e}\nОтвет:\n{content}"
        )
    
    return data
