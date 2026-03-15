import argparse
import sys
import uuid

import requests
import urllib3
from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage

from config import Config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"

PROMPT = (
    "Посмотри на это изображение туристического постера. "
    "Определи место, которое на нём изображено. "
    "Ответь строго в формате JSON (без markdown-обёртки) со следующими полями: "
    '"location" — название места, '
    '"country" — страна, '
    '"description" — краткое описание (3-5 предложений): '
    "обязательно укажи конкретные достопримечательности, объекты или природные особенности, "
    "которые видны на изображении (например, башни, мосты, храмы, горы), "
    "а также почему это место примечательно как туристическое направление; "
    '"nearby_attractions" — список из 1-3 основных достопримечательностей '
    "поблизости от изображённого места (название и одно предложение о каждой). "
    "Весь текст должен быть на русском языке."
)


class ImageDescriber:
    def __init__(self, config: Config):
        self.config = config
        self.giga = GigaChat(
            model="GigaChat-2-Pro",
            credentials=config.gigachat_api_key,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
        )

    def _get_access_token(self) -> str:
        response = requests.post(
            GIGACHAT_AUTH_URL,
            headers={
                "Authorization": f"Basic {self.config.gigachat_api_key}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            data={"scope": "GIGACHAT_API_PERS"},
            verify=False,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _delete_file(self, file_id: str):
        token = self._get_access_token()
        response = requests.post(
            f"{GIGACHAT_BASE_URL}/files/{file_id}/delete",
            headers={"Authorization": f"Bearer {token}"},
            verify=False,
        )
        response.raise_for_status()

    def describe(self, image_path: str, user_comment: str | None = None) -> str:
        with open(image_path, "rb") as f:
            file_obj = self.giga.upload_file(f)

        if not file_obj:
            raise RuntimeError(f"Failed to upload file: {image_path}")

        content = PROMPT
        if user_comment:
            content = (
                f"Комментарий пользователя к изображению (учитывай при определении места): {user_comment}\n\n"
                + content
            )

        try:
            message = HumanMessage(
                content=content,
                additional_kwargs={"attachments": [file_obj.id_]},
            )
            response = self.giga.invoke([message])
        finally:
            self._delete_file(file_obj.id_)

        return response.content


def main():
    parser = argparse.ArgumentParser(description="Описание места на изображении туристического постера.")
    parser.add_argument("image_path", help="Путь к изображению")
    parser.add_argument(
        "comment",
        nargs="?",
        default=None,
        help="Опциональный комментарий к изображению (помогает точнее определить место)",
    )
    args = parser.parse_args()

    config = Config()
    describer = ImageDescriber(config)

    print("Analyzing image...")
    description = describer.describe(args.image_path, args.comment)
    print(f"\n{description}")


if __name__ == "__main__":
    main()
