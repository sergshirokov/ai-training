from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from settings import *

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["source_text"],
    template="""
Ты опытный переводчик технических текстов, сделай перевод текста пользователя на английский

Текст пользователя: {source_text}

Ответ дай только переведенный текст, не добавляй ничего лишнего, только перевод.
"""
)

def translate_text(input_file: Path, output_file: Path, model: str = "gpt-4o-mini") -> None:
    print(f"Перевод текста: {input_file} -> {output_file}")

    llm = ChatOpenAI(
        model_name=model,
        temperature=0.1,
        openai_api_key=OPENAI_API_KEY
    )

    chain = SYSTEM_PROMPT | llm

    source_text = input_file.read_text(encoding='utf-8')

    response = chain.invoke({"source_text": source_text})

    output_file.write_text(response.text, encoding="utf-8")

    print(f"Перевод сохранен в: {output_file}")

    return