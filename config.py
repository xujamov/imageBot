# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
#
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GENERATIVEAI_API_KEY = os.getenv("GENERATIVEAI_API_KEY")
