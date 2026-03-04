import argparse
from pathlib import Path

from stt import transcribe_audio
from translate import translate_text
from tts import text_to_speech
from langchain_image_generation_pipeline import create_illustration

def main():
    parser = argparse.ArgumentParser(
        description="Утилита для перевода русской озвучки в английскую (STT->Translate->TTS)"
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Путь к входному аудио/видео файлу (например, WAV/MP3/OGG)",
    )
    parser.add_argument(
        "output_folder",
        type=Path,
        help="Папка для сохранения выходных данных (транскрибация, перевод, аудиотрек)",
    )

    args = parser.parse_args()

    if not args.input_file.exists():
        raise SystemExit(f"Файл не найден: {args.input_file}")

    transcript = args.output_folder / "transcription.txt"
    transcribe_audio(args.input_file, transcript)
 
    translate = args.output_folder / "translate.txt"
    translate_text(transcript, translate)

    speech = args.output_folder / "speech.mp3"
    text_to_speech(translate, speech)

    source_text = translate.read_text(encoding='utf-8')
    illustration = args.output_folder / "image.png"
    create_illustration(source_text, illustration)

    print("Done")
    
if __name__ == "__main__":
    main()