#!/usr/bin/env python3

# Telegram bot for Craiyon Image generator

# Imports
import requests
import telebot
import base64
import json
import os
import sys

# Token
Token = "7663625947:AAEi-8ywV_oWt9LoLugowF2obO6tRq2CgKU"

# Initialize bot
bot = telebot.TeleBot(Token)

# User class for handling user data
class User:
    def __init__(self, message) -> None:
        # Retrieves user info from the message
        self.fname = message.from_user.first_name
        self.lname = message.from_user.last_name
        self.uname = message.from_user.username
        self.usrid = message.from_user.id

# Craiyon class for generating images based on prompt
class Craiyon:
    def __init__(self, prompt):
        self.prompt = prompt

    # Generates and saves images
    def generate(self):
        craiyon_api_url = "https://backend.craiyon.com/generate"
        payload = {"prompt": self.prompt}
        
        # Create 'generated' directory if it does not exist
        if not os.path.exists("generated"):
            os.makedirs("generated")

        try:
            response = requests.post(url=craiyon_api_url, json=payload, timeout=160)
            result = response.json().get("images", [])
            
            for index, image in enumerate(result, start=1):
                image_path = f"generated/{self.prompt}_{index}.webp"
                with open(image_path, "wb") as file:
                    file.write(base64.decodebytes(image.encode("utf-8")))
            return True  # Indicate success

        except Exception as ex:
            print(f"Error generating images: {ex}")
            return False  # Indicate failure

# LOCKER for handling single-user access at a time
status = False

def lock():
    global status
    status = True

def unlock():
    global status
    status = False

# Start command to welcome the user
@bot.message_handler(commands=["start"])
def start_command(message):
    user = User(message)
    name = user.fname if user.fname is not None else "User"
    bot.reply_to(message, f"Hello {name}! Use 'ai your text' to generate images.")

# Craiyon image generator handler
@bot.message_handler(func=lambda message: message.text.lower().startswith("ai"))
def craiyon_generator(message):
    global status
    if not status:
        lock()

        user = User(message)
        name = user.fname if user.fname is not None else "User"
        prompt_text = message.text[3:].strip()  # Get the prompt text after 'ai'
        
        if not prompt_text:
            bot.reply_to(message, "Please provide some text after 'ai' to generate an image.")
            unlock()
            return

        waiting_message = bot.reply_to(message, "Generating images... This may take up to 3 minutes.")
        
        # Clear old images if any
        for file_name in os.listdir("generated"):
            os.remove(os.path.join("generated", file_name))

        # Generate new images
        generator = Craiyon(prompt_text)
        if generator.generate():
            for file_name in os.listdir("generated"):
                with open(f"generated/{file_name}", "rb") as img:
                    bot.send_photo(message.chat.id, img, caption=file_name.split(".webp")[0])
            bot.delete_message(message.chat.id, waiting_message.message_id)
        else:
            bot.edit_message_text("Could not generate images. Please try again later.", message.chat.id, waiting_message.message_id)

        unlock()
    else:
        bot.reply_to(message, "Another user is using this feature. Please wait...")

# Run the bot
if __name__ == "__main__":
    try:
        print("Bot is running...")
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("Bot has been stopped.")
        sys.exit()
