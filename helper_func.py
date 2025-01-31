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

async def broadcast_message(client: Client, message: str):
    """Send a broadcast message to all users."""
    from database import all_users  # Import function to get all users from the database
    
    # Get all user IDs from the database
    user_ids = all_users()

    for user_id in user_ids:
        try:
            await client.send_message(user_id, message)
            print(f"Message sent to {user_id}")
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}")
