from pathlib import Path
from openai import OpenAI

from settings import *

def text_to_speech(input_file: Path, output_file: Path, model: str = "gpt-4o-mini-tts", voice: str = "cedar") -> None:
    print(f"Озвучка текста: {input_file} -> {output_file}")

    source_text = input_file.read_text(encoding='utf-8')

    client = OpenAI()

    # Используем потоковую запись в файл, чтобы не держать аудио в памяти
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=source_text,
    ) as response:
        response.stream_to_file(str(output_file))

    print(f"Аудио сохранено в: {output_file}")

    return