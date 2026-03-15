import argparse
import json
import sys
from collections.abc import Callable

from config import Config
from describe import ImageDescriber
from generate import PosterGenerator


class PosterPipeline:
    def __init__(self, config: Config):
        self.config = config
        self.describer = ImageDescriber(config)
        self.generator = PosterGenerator(config)

    def _extract_fields(self, data: dict) -> dict:
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

    def _format_description(self, data: dict) -> str:
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

    def run(
        self,
        image_path: str,
        comment: str | None = None,
        progress_callback: Callable[[str], None] | None = None,
    ) -> str:
        def report(msg: str) -> None:
            if progress_callback:
                progress_callback(msg)
            else:
                print(msg)

        report("Анализ изображения...")
        raw = self.describer.describe(image_path, comment)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            report("Ошибка: модель вернула не-JSON.")
            print(raw)
            sys.exit(1)

        fields = self._extract_fields(data)
        if not progress_callback:
            print(self._format_description(fields))

        report("Генерация открытки...")
        filepath = self.generator.run(fields)
        report("Готово.")
        description_text = self._format_description(fields)
        if not progress_callback:
            print(description_text)
            print(f"\nPipeline complete! Postcard saved to: {filepath}")
        return filepath, description_text


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
    pipeline = PosterPipeline(config)
    pipeline.run(args.image_path, args.comment)


if __name__ == "__main__":
    main()
