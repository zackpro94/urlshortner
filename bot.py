import telebot
import requests
import sqlite3
import re
import time

# Replace with your Telegram bot token
BOT_TOKEN = "###################"

bot = telebot.TeleBot(BOT_TOKEN)

# Database setup
def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        long_url TEXT NOT NULL,
        short_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_url(long_url, short_url):
    """Save shortened URL to the database."""
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO urls (long_url, short_url) VALUES (?, ?)", (long_url, short_url))
    conn.commit()
    conn.close()

def get_stats():
    """Get the total number of shortened URLs."""
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM urls")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# URL Validation
def is_valid_url(url):
    """Check if the input is a valid URL."""
    regex = re.compile(r'^(https?:\/\/)?(www\.)?[\w\-]+(\.[\w\-]+)+[/#?]?.*$')
    return re.match(regex, url) is not None

# TinyURL API
def shorten_url(long_url):
    """Shorten the URL using TinyURL API."""
    url = f"https://tinyurl.com/api-create.php?url={long_url}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.text  # TinyURL returns the short URL directly
    else:
        return None

# Start Command
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "🚀 Welcome! Send me any URL, and I'll shorten it for you!\n"
        "📌 Use /stats to check how many links have been shortened."
    )

# Stats Command
@bot.message_handler(commands=['stats'])
def stats_message(message):
    count = get_stats()
    bot.send_message(message.chat.id, f"📊 Total links shortened: {count}")

# Handle Messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    long_url = message.text.strip()
    
    if is_valid_url(long_url):
        short_url = shorten_url(long_url)
        if short_url:
            save_url(long_url, short_url)
            bot.send_message(message.chat.id, f"✅ Shortened URL: {short_url}")
        else:
            bot.send_message(message.chat.id, "❌ Error: Could not shorten the URL.")
    else:
        bot.send_message(message.chat.id, "⚠ Please send a valid URL.")

# Inline Mode (for direct link shortening)
@bot.inline_handler(lambda query: len(query.query) > 0)
def inline_query(query):
    long_url = query.query.strip()

    if is_valid_url(long_url):
        short_url = shorten_url(long_url)
        if short_url:
            save_url(long_url, short_url)
            result = telebot.types.InlineQueryResultArticle(
                id=str(time.time()),
                title="Shortened URL",
                description=short_url,
                input_message_content=telebot.types.InputTextMessageContent(short_url)
            )
            bot.answer_inline_query(query.id, [result])
        else:
            bot.answer_inline_query(query.id, [])
    else:
        bot.answer_inline_query(query.id, [])

# Initialize DB and start bot
init_db()
bot.polling()
