from pathlib import Path
from openai import OpenAI

from settings import *

def transcribe_audio(input_file: Path, output_file: Path, model: str = "gpt-4o-mini-transcribe") -> None:
    print(f"Транскрибация аудио: {input_file} -> {output_file}")

    client = OpenAI()

    with input_file.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=model,
            file=audio_file,
        )

    output_file.write_text(transcription.text, encoding="utf-8")
    print(f"Транскрипция сохранена в: {output_file}")

    return