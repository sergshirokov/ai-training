import argparse
import json
import sys

from config import Config
from describe import ImageDescriber
from generate import PosterGenerator


def extract_fields(data: dict) -> dict:
    """Restructure model output into a dict with predictable Latin keys."""
    fields = {"location": "N/A", "country": "N/A", "description": "", "nearby_attractions": []}
    for value in data.values():
        if isinstance(value, list):
            fields["nearby_attractions"] = value
    for key, value in data.items():
        if not isinstance(value, str):
            continue
        ascii_key = key.encode("ascii", "ignore").decode().strip("_").lower()
        if ascii_key in fields:
            fields[ascii_key] = value
    return fields


def format_description(data: dict) -> str:
    lines = [
        f"Место: {data['location']}",
        f"Страна:  {data['country']}",
        "",
        data["description"],
    ]

    attractions = data.get("nearby_attractions") or []
    if attractions:
        lines.append("")
        lines.append("Достопримечательности поблизости:")
        for i, item in enumerate(attractions, 1):
            lines.append(f"  {i}. {item}")

    return "\n".join(lines)



def main():
    parser = argparse.ArgumentParser(description="Описание изображения и генерация открытки.")
    parser.add_argument("image_path", help="Путь к изображению")
    parser.add_argument(
        "comment",
        nargs="?",
        default=None,
        help="Опциональный комментарий к изображению",
    )
    args = parser.parse_args()

    config = Config()
    describer = ImageDescriber(config)
    generator = PosterGenerator(config)

    print("Step 1: Analyzing image...\n")
    raw = describer.describe(args.image_path, args.comment)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("Model returned non-JSON response:")
        print(raw)
        sys.exit(1)

    fields = extract_fields(data)

    print(format_description(fields))

    print("\n\nStep 2: Generating travel postcard...\n")
    filepath = generator.run(fields)

    print(f"\nPipeline complete! Postcard saved to: {filepath}")


if __name__ == "__main__":
    main()
