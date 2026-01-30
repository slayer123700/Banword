import logging
import asyncio
import aiohttp
import io
import time
from PIL import Image
from pyrogram import Client, filters
from pyrogram.types import Message
from Zero.utils.decorators import AdminRights
from Nexa.database.client import (
    set_nsfw_status, 
    get_nsfw_status, 
    get_cached_scan, 
    cache_scan_result
)

logger = logging.getLogger(name)
NSFW_API_URL = "https://nexacoders-nexa-api.hf.space/scan"

# Global Session
ai_session = None

async def get_session():
    global ai_session
    if ai_session is None or ai_session.closed:
        ai_session = aiohttp.ClientSession()
    return ai_session

# --- OPTIMIZATION ENGINE ---

def optimize_image(image_bytes: bytes) -> bytes:
    """
    Hyper-Fast Optimization:
    1. If file < 50KB, return immediately (Don't waste CPU).
    2. Else, resize to 256px JPEG (Fastest for AI).
    """
    if len(image_bytes) < 50 * 1024:
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGB")
        img.thumbnail((256, 256)) # 256px is standard for ViT models
        out_io = io.BytesIO()
        img.save(out_io, format='JPEG', quality=80)
        return out_io.getvalue()
    except Exception:
        return image_bytes # Fallback if error

# --- FORMATTING ---

def format_scores_ui(scores: dict) -> str:
    icons = {"porn": "🔞", "hentai": "👾", "sexy": "💋", "neutral": "😐", "drawings": "🎨"}
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    text_lines = []
    for label, score in sorted_scores:
        icon = icons.get(label, "🔸")
        text_lines.append(f"{icon} {label.title().ljust(10)} : {score * 100:05.2f}%")

    return "\n".join(text_lines)


# --- 1. SETTINGS ---

@Client.on_message(filters.command("nsfw") & filters.group)
@AdminRights("can_change_info")
async def nsfw_toggle_command(client: Client, message: Message):
    if len(message.command) < 2:
        status = await get_nsfw_status(message.chat.id)
        state = "Enabled" if status else "Disabled"
        await message.reply_text(f"🚀 NSFW System: {state}\nUsage: /nsfw on or /nsfw off")
        return

    action = message.command[1].lower()
    if action in ["on", "enable", "true"]:
        await set_nsfw_status(message.chat.id, True)
        await message.reply_text("🚀 NSFW Active. Scanning in Hyper-Speed Mode.")
    elif action in ["off", "disable", "false"]:
        await set_nsfw_status(message.chat.id, False)
        await message.reply_text("💤 NSFW Paused.")


# --- 2. MANUAL SCAN (/scan) ---

@Client.on_message(filters.command("scan"))
async def manual_scan_command(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("⚠️ Reply to media.")
        return

    msg_to_scan = message.reply_to_message
    status_msg = await message.reply_text("⚡ Scanning...")

    start = time.time()
    is_nsfw, data, reason = await process_media_scan(client, msg_to_scan, manual_override=True)
    taken = time.time() - start

    if data:
        score_block = format_scores_ui(data.get("scores", {}))
        header = "🚨 UNSAFE" if is_nsfw else "✅ SAFE"
        color = "🟥" if is_nsfw else "🟩"

        result_text = (
            f"{header}\n"
            f"⏱️ Time: {taken:.3f}s\n"
            f"🔎 Verdict: {reason}\n"
            f"{color * 12}\n\n"
            f"📊 Confidence Scores:\n"
            f"{score_block}"
        )
        await status_msg.edit_text(result_text)
    else:
        await status_msg.edit_text("❌ Scan Failed.")


# --- 3. AUTO WATCHER ---

@Client.on_message(filters.group & (filters.photo | filters.sticker | filters.document), group=5)
async def nsfw_watcher(client: Client, message: Message):
    if not await get_nsfw_status(message.chat.id):
        return 

    is_nsfw, data, reason = await process_media_scan(client, message, manual_override=False)

    if is_nsfw and data:
        await handle_nsfw_detection(client, message, data, reason)


# --- 4. CORE ENGINE ---
