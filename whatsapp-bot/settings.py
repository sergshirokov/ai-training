import os
from dotenv import load_dotenv

load_dotenv()

VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
WHATSAPP_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

PORT = os.getenv('PORT')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
