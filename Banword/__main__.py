import logging
from dotenv import load_dotenv
from pyrogram import idle
from config import API_ID, API_HASH, BOT_TOKEN

from Banword import app  # IMPORTANT: import the SAME app

load_dotenv()

logging.basicConfig(
    format="[%(levelname)s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)

def main():
    app.start()
    print("✅ Bot started successfully")
    idle()          # 🔥 THIS LINE WAS MISSING
    app.stop()

if __name__ == "__main__":
    main()
