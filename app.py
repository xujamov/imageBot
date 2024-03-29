import logging
import os
import uuid

from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from pathlib import Path
import google.generativeai as genai
from config import TELEGRAM_BOT_TOKEN, GENERATIVEAI_API_KEY

genai.configure(api_key=GENERATIVEAI_API_KEY)

# Set up the model
generation_config = {
  "temperature": 0.4,
  "top_p": 1,
  "top_k": 32,
  "max_output_tokens": 4096,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  }
]

model = genai.GenerativeModel(model_name="gemini-pro-vision",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

PHOTO, LOCATION, BIO = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text(
        "Salom! Mening ismim Vision Bot. "
        "Menga fotosurat yuboring, men buni siz uchun tasvirlab beraman!\n\n"
    )

    return PHOTO


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and answer."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    myuuid = uuid.uuid4()
    image_name = f"{myuuid}.jpeg"
    await photo_file.download_to_drive(image_name)
    logger.info("Photo of %s: %s", user.first_name, image_name)
    answer = photo_answer(image_name)
    await update.message.reply_text(answer)

    # Remove the image file after processing
    remove_image(image_name)
    return PHOTO


def photo_answer(image):
    # Validate that an image is present
    if not (img := Path(image)).exists():
        raise FileNotFoundError(f"Could not find image: {img}")

    image_parts = [
        {
            "mime_type": "image/jpeg",
            "data": Path(image).read_bytes()
        },
    ]

    prompt_parts = [
        image_parts[0],
        "\nWhat do you think about this photo? Describe and explain it. If it is question then solve it. Translate your answer into Russian and Uzbek.\n",
    ]

    response = model.generate_content(prompt_parts)
    return response.text

def remove_image(image_name):
    # Validate that an image is present
    img_path = Path(image_name)
    if not img_path.exists():
        raise FileNotFoundError(f"Could not find image: {img_path}")

    # Remove the image file
    os.remove(img_path)
    logger.info("Removed image: %s", img_path)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Xayr! Umid qilamanki, bir kun yana gaplashamiz.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add conversation handler with the states PHOTO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, photo), CommandHandler("photo", photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
