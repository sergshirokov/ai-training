import argparse
import json

from doc_extractor import *

def main():
    parser = argparse.ArgumentParser(
        description="Утилита для извлечения и анализа данных сканов и изображений с помощью мультимодальных LLM"
    )

    parser.add_argument(
        "image_path",
        help="Путь к изображению (jpg, jpeg, png и т.п.)",
    )
    parser.add_argument(
        "--datatype",
        default="doc",
        help="Тип извлекаемых данных",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Имя модели OpenAI с поддержкой vision (по умолчанию: gpt-4o).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Вывести JSON с отступами (читаемый вид).",
    )

    args = parser.parse_args()

    if args.datatype == "doc":
        data = extract_document(args.image_path, model=args.model)
    else:
        raise RuntimeError("Такой тип входных данных не поддерживается.")

    if args.pretty:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(data, ensure_ascii=False))

if __name__ == "__main__":
    main()