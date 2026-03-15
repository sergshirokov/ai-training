import base64
import json
import os
import sys
from datetime import datetime

import httpx
from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage
from openai import OpenAI

from config import Config

OUTPUT_DIR = "output"

SYSTEM_PROMPT = (
    "You are an expert travel postcard designer. "
    "The user will provide a JSON object with fields: "
    "location, country, description, and nearby_attractions (a list of landmarks). "
    "Your task is to create a vivid, detailed prompt for an AI image generator "
    "that will produce a bright, vibrant travel poster with rich saturated colors. "
    "LAYOUT: the poster is divided into clearly separated panels or inset frames — "
    "the main location occupies the large hero area at the top, "
    "and each landmark from nearby_attractions is shown in its own smaller panel or vignette below, "
    "like a postcard grid or picture-in-picture layout. "
    "Each panel must show ONLY ONE real landmark as it actually looks, with NO text or captions on the panels. "
    "Do NOT merge or blend landmarks together into a single scene — "
    "they must be visually distinct and separately identifiable. "
    "TEXT ON THE POSTER: only ONE short title is allowed — the name of the main location. "
    "This title MUST be in Latin script only (use transliteration or English name, e.g. Shanghai, Pudong, not Cyrillic). "
    "No other text, labels, or captions anywhere on the image. "
    "Include bold color palette, artistic style, lighting, and atmosphere. "
    "IMPORTANT: the image canvas is portrait 1024x1536 pixels. "
    "The entire composition must fit fully within the frame with comfortable margins. "
    "Nothing should be cropped or extend beyond the edges. "
    "Reply ONLY with the image-generation prompt, nothing else."
)


class PosterGenerator:
    def __init__(self, config: Config):
        self.config = config
        self.llm = GigaChat(
            model="GigaChat-2",
            credentials=config.gigachat_api_key,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            timeout=120,
        )
        self.image_client = OpenAI(api_key=config.openai_api_key)

    def enhance_prompt(self, description: dict) -> str:
        user_content = json.dumps(description, ensure_ascii=False, indent=2)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]
        try:
            return self.llm.invoke(messages).content
        except httpx.ConnectTimeout:
            raise RuntimeError(
                "Таймаут подключения к GigaChat. Проверьте интернет, VPN и доступ к api.sberbank.ru. Попробуйте позже."
            ) from None

    def generate_image(self, prompt: str) -> bytes:
        response = self.image_client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1536",
        )
        return base64.b64decode(response.data[0].b64_json)

    def save_image(self, image_data: bytes) -> str:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(OUTPUT_DIR, f"poster_{timestamp}.png")
        with open(filepath, "wb") as f:
            f.write(image_data)
        return filepath

    def run(self, description: dict) -> str:
        print("Enhancing prompt with GigaChat...")
        enhanced = self.enhance_prompt(description)
        print(f"\nEnhanced prompt:\n{enhanced}\n")

        print("Generating image with gpt-image-1...")
        image_data = self.generate_image(enhanced)

        filepath = self.save_image(image_data)
        print(f"\nDone! Image saved to: {filepath}")
        return filepath


def main():
    config = Config()
    generator = PosterGenerator(config)

    prompt = input("Enter location JSON or short description: ").strip()
    if not prompt:
        print("Empty input, exiting.")
        sys.exit(1)

    try:
        data = json.loads(prompt)
    except json.JSONDecodeError:
        data = {"location": prompt, "country": "", "description": prompt, "nearby_attractions": []}

    generator.run(data)


if __name__ == "__main__":
    main()
