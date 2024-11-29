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
        "<b>Welcome to the bot, I can add channel username to every new post in your channel!</b>\n\n"
        "<b>Contact my developer to get more info about me.</b>\n\n"
        "<blockquote><b>@Ur_amit_01 🥀</b></blockquote>*"
    )
    keyboard = {
        "inline_keyboard": [[
            {"text": "Developer 🪷", "url": "https://t.me/Ur_Amit_01"}
        ]]
    }
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "reply_markup": json.dumps(keyboard)}
    requests.post(url, data=data)

def send_message(chat_id, text):
    token = 'BOT_TOKEN'  # Replace with your bot token
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=payload)

def get_custom_caption(chat_id):
    # For now, let's just return a default caption
    return "Default caption" 
    
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update and update["message"].get("text") == "/start":
        send_start_message(update["message"]["chat"]["id"])

    if "message" in update and "text" in update["message"]:
        # Check if the message contains the /setcaption command
        if update["message"]["text"].startswith("/setcaption"):
            caption = update["message"]["text"][12:].strip()  # Extract caption after the command
            if caption:
                # Store the caption or associate it with the chat_id (this depends on your use case)
                save_custom_caption(update["message"]["chat"]["id"], caption)
                send_message(update["message"]["chat"]["id"], "Custom caption set successfully!")
            else:
                send_message(update["message"]["chat"]["id"], "Please provide a caption after the command.")

    if "channel_post" in update:
        post = update["channel_post"]
        chat_id = post["chat"]["id"]
        message_id = post["message_id"]

        # HTML formatting for bold and quote
        quoted_channel_username = f"<blockquote><b>{CHANNEL_USERNAME}</b></blockquote>"

        # Check if a custom caption is available for this chat
        custom_caption = get_custom_caption(chat_id)

        if "text" in post:
            # Apply custom caption if available and add quoted channel username
            new_text = post["text"] + f"\n\n{quoted_channel_username}"
            new_caption = custom_caption + f"\n\n{quoted_channel_username}" if custom_caption else quoted_channel_username
            edit_message(chat_id, message_id, new_text=new_text, parse_mode="HTML")
        elif "caption" in post:
            # Apply custom caption if available and add quoted channel username
            new_caption = post["caption"] + f"\n\n{quoted_channel_username}"
            if custom_caption:
                new_caption = custom_caption + f"\n\n{quoted_channel_username}"
            edit_message(chat_id, message_id, new_caption=new_caption, parse_mode="HTML")

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
