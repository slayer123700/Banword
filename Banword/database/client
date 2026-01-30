from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import config

# ================= CONFIG =================

MONGO_URI = config.MONGO_URI
MONGO_DB = getattr(config, "MONGO_DB", "telegram_bot")

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo[MONGO_DB]

nsfw_settings = db.nsfw_settings
scan_cache = db.nsfw_scan_cache


# ================= INIT =================

async def init_db():
    """
    Initialize database indexes
    Call this once on startup
    """

    # Per-chat NSFW toggle
    await nsfw_settings.create_index(
        "chat_id",
        unique=True,
        background=True
    )

    # Image scan cache
    await scan_cache.create_index(
        "file_unique_id",
        unique=True,
        background=True
    )

    await scan_cache.create_index(
        "is_nsfw",
        background=True
    )

    # Auto-cleanup cache after 7 days
    await scan_cache.create_index(
        "created_at",
        expireAfterSeconds=60 * 60 * 24 * 7,
        background=True
    )


# ================= NSFW SETTINGS =================

async def set_nsfw_status(chat_id: int, status: bool):
    """
    Enable / Disable NSFW system for a chat
    """
    await nsfw_settings.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "enabled": bool(status),
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )


async def get_nsfw_status(chat_id: int) -> bool:
    """
    Returns True if NSFW system is enabled
    """
    data = await nsfw_settings.find_one({"chat_id": chat_id})
    if not data:
        return False
    return bool(data.get("enabled", False))


# ================= FAST SCAN CACHE =================

async def cache_scan_result(
    file_unique_id: str,
    is_safe: bool,
    data: dict
):
    """
    Store scan result for instant decision next time
    """
    await scan_cache.update_one(
        {"file_unique_id": file_unique_id},
        {
            "$set": {
                "is_nsfw": not is_safe,
                "data": data or {},
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )


async def get_cached_scan(file_unique_id: str):
    """
    Fetch cached scan if exists
    """
    return await scan_cache.find_one(
        {"file_unique_id": file_unique_id}
    )
