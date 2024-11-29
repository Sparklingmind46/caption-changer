import os
import json
import requests
import logging
from flask import Flask, request

app = Flask(__name__)

# Get environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Your bot token
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")  # Your channel username

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Function to send a start message with a developer button
def send_start_message(chat_id):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    text = (
        "*Welcome to the bot, I can add channel username to every new post in your channel!*\n\n"
        "*Contact my developer to get more info about me.*\n\n"
        "> *@Ur_Amit_01*"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": "Developer 🤖", "url": "https://t.me/Ur_Amit_01"}
        ]]
    }
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "reply_markup": json.dumps(keyboard)}
    requests.post(url, data=data)


@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update and update["message"].get("text") == "/start":
        send_start_message(update["message"]["chat"]["id"])

    if "channel_post" in update:
        post = update["channel_post"]
        chat_id = post["chat"]["id"]
        message_id = post["message_id"]

        # Escape any special characters in the channel username
        quoted_channel_username = f"> *{CHANNEL_USERNAME}*"
        quoted_channel_username = quoted_channel_username.replace("_", "\\_").replace("*", "\\*").replace("[", "\").replace("]", "\").replace("(", "\").replace(")", "\")

        if "text" in post:
            # Bold and quote the channel username using MarkdownV2
            new_text = post["text"] + f"\n\n{quoted_channel_username}"
            edit_message(chat_id, message_id, new_text=new_text, parse_mode="MarkdownV2")
        elif "caption" in post:
            # Bold and quote the channel username using MarkdownV2
            new_caption = post["caption"] + f"\n\n{quoted_channel_username}"
            edit_message(chat_id, message_id, new_caption=new_caption, parse_mode="MarkdownV2")

    return "OK", 200
    
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to edit message text or caption
def edit_message(chat_id, message_id, new_text=None, new_caption=None, parse_mode=None):
    if new_text:
        url = f"{TELEGRAM_API_URL}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": new_text,
            "parse_mode": parse_mode
        }
    elif new_caption:
        url = f"{TELEGRAM_API_URL}/editMessageCaption"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "caption": new_caption,
            "parse_mode": parse_mode
        }
    else:
        raise ValueError("Either new_text or new_caption must be provided.")
    
    response = requests.post(url, data=data)
    
    if response.status_code != 200:
        logger.error(f"Error editing message: {response.status_code} - {response.text}")
    else:
        logger.info(f"Message edited successfully: {response.json()}")
    return response.json()

# Function to set the webhook
def set_webhook():
    webhook_url = os.getenv("WEBHOOK_URL")  # Your Koyeb app's public URL
    if not webhook_url:
        raise ValueError("WEBHOOK_URL is not set in environment variables.")
    
    url = f"{TELEGRAM_API_URL}/setWebhook"
    data = {"url": webhook_url}
    response = requests.post(url, data=data)
    
    if response.status_code != 200:
        raise RuntimeError(f"Failed to set webhook: {response.text}")
    return response.json()

@app.route("/health", methods=["GET"])
def health_check():
    return "OK", 200

if __name__ == "__main__":
    # Set webhook when the script starts
    logger.info("Setting webhook...")
    result = set_webhook()
    logger.info(f"Webhook set: {result}")
    app.run(host="0.0.0.0", port=5000)
