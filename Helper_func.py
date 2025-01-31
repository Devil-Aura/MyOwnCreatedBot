from pyrogram import Client
from database import all_users, is_broadcast_disabled

async def broadcast_message(client: Client, message: str):
    users = all_users()  # Get all users
    for user in users:
        user_id = user['user_id']
        # Check if broadcast is disabled for the user
        if is_broadcast_disabled(user_id):
            continue
        try:
            await client.send_message(user_id, message)
        except Exception as e:
            print(f"Error sending message to {user_id}: {e}")
