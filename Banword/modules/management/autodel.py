import asyncio
from pyrogram import filters
from pyrogram.types import Message
from Banword import app

# chat_id : delete_after_seconds
AUTO_DELETE_TIME = {}


# ==============================
# Set auto-delete time
# /setdel <seconds>
# ==============================
@app.on_message(filters.command("setdel") & filters.group)
async def set_auto_delete(client, message: Message):
    if not message.from_user:
        return

    member = await client.get_chat_member(
        message.chat.id, message.from_user.id
    )

    if member.status not in ("administrator", "creator"):
        return await message.reply_text("❌ Only admins can use this")

    if len(message.command) < 2:
        return await message.reply_text("Usage: /setdel <seconds>")

    try:
        seconds = int(message.command[1])
        if seconds < 1:
            raise ValueError
    except ValueError:
        return await message.reply_text("❌ Time must be a number (seconds)")

    AUTO_DELETE_TIME[message.chat.id] = seconds
    await message.reply_text(
        f"✅ Auto-delete enabled\n"
        f"🕒 Every new message will be deleted after **{seconds} seconds**"
    )


# ==============================
# Disable auto-delete
# /deldisable
# ==============================
@app.on_message(filters.command("deldisable") & filters.group)
async def disable_auto_delete(client, message: Message):
    if not message.from_user:
        return

    member = await client.get_chat_member(
        message.chat.id, message.from_user.id
    )

    if member.status not in ("administrator", "creator"):
        return await message.reply_text("❌ Only admins can use this")

    AUTO_DELETE_TIME.pop(message.chat.id, None)
    await message.reply_text("🚫 Auto-delete disabled for this chat")


# ==============================
# PER-MESSAGE AUTO DELETE
# ==============================
@app.on_message(filters.group & ~filters.service)
async def auto_delete_handler(client, message: Message):
    chat_id = message.chat.id

    if chat_id not in AUTO_DELETE_TIME:
        return

    delay = AUTO_DELETE_TIME[chat_id]

    await asyncio.sleep(delay)

    try:
        await message.delete()
    except:
        pass
