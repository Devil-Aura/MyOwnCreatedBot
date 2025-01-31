from pyrogram import Client
import logging

logger = logging.getLogger(__name__)

async def is_user_subscribed(client: Client, user_id: int, channel_username: str) -> bool:
    try:
        user = await client.get_chat_member(channel_username, user_id)
        return user.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
        return False
