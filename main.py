import telebot
from pymongo import MongoClient
import os

# Initialize Bot and MongoDB client
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
BROADCAST_CHANNEL_ID = os.getenv("BROADCAST_CHANNEL_ID")  # Optional broadcast channel ID
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID"))  # Replace with your admin user ID or set it as an environment variable

bot = telebot.TeleBot(BOT_TOKEN)
client = MongoClient(MONGO_URI)
db = client['telegram_bot']
caption_collection = db['captions']
user_collection = db['users']  # MongoDB collection to store user IDs

# Store user ID when they start the bot
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Save the user ID and username to MongoDB if not already saved
    if not user_collection.find_one({"user_id": user_id}):
        user_collection.insert_one({"user_id": user_id, "username": username})
    
    bot.reply_to(message, "Welcome to the bot!")

# Command to set a custom caption, working in any channel
@bot.message_handler(commands=['setcaption'], func=lambda message: message.chat.type == 'channel')
def set_caption(message):
    channel_id = message.chat.id
    caption = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    
    if caption:
        # Save or update custom caption for the channel
        caption_collection.update_one({"channel_id": channel_id}, {"$set": {"caption": caption}}, upsert=True)
        bot.reply_to(message, f"Custom caption set to: {caption}")
        
        # Optionally notify the broadcast channel
        if BROADCAST_CHANNEL_ID:
            bot.send_message(BROADCAST_CHANNEL_ID, f"Custom caption set in channel {channel_id}: {caption}")
    else:
        bot.reply_to(message, "Please provide a caption after the command.")

# Command to clear the custom caption in the channel
@bot.message_handler(commands=['clearcaption'], func=lambda message: message.chat.type == 'channel')
def clear_caption(message):
    channel_id = message.chat.id
    caption_collection.delete_one({"channel_id": channel_id})
    bot.reply_to(message, "The custom caption for this channel has been cleared.")
    
    # Optionally notify the broadcast channel
    if BROADCAST_CHANNEL_ID:
        bot.send_message(BROADCAST_CHANNEL_ID, f"Custom caption cleared in channel {channel_id}")

# Monitor for new media or files in any channel
@bot.channel_post_handler(content_types=['document', 'photo', 'video', 'audio'])
def handle_new_media(message):
    # Get file information
    channel_id = message.chat.id
    file_name = getattr(message.document, 'file_name', 'media_file')  # Use media_file if no filename is present
    current_caption = message.caption if message.caption else ""

    # Fetch the custom caption for this channel, if it exists
    custom_caption_data = caption_collection.find_one({"channel_id": channel_id})
    custom_caption = custom_caption_data["caption"] if custom_caption_data else ""

    # If there's a custom caption, replace {filename} with the actual file name and {caption} with the existing caption (if any)
    if custom_caption:
        caption_to_use = custom_caption.replace("{filename}", file_name).replace("{caption}", current_caption)
        bot.edit_message_caption(chat_id=channel_id, message_id=message.message_id, caption=caption_to_use)
        
        # Optionally notify the broadcast channel
        if BROADCAST_CHANNEL_ID:
            bot.send_message(BROADCAST_CHANNEL_ID, f"File updated in channel {channel_id} with caption: {caption_to_use}")
    else:
        bot.reply_to(message, "No custom caption set for this channel.")

# Function to send a message to all users who have started the bot
def send_message_to_all_users(message_text):
    users = user_collection.find()  # Fetch all users who started the bot
    for user in users:
        try:
            bot.send_message(user['user_id'], message_text)
        except telebot.apihelper.ApiException as e:
            print(f"Failed to send message to {user['user_id']}: {e}")

# Admin-only command to broadcast a message to all users
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == ADMIN_USER_ID:
        message_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "No message provided"
        send_message_to_all_users(message_text)
        bot.reply_to(message, "Broadcast message sent to all users.")
    else:
        bot.reply_to(message, "You are not authorized to broadcast messages.")

# Start polling
bot.polling()
