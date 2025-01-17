import logging
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import cfg
from database import (
    add_user, add_group, all_users, all_groups,
    remove_user, ban_user, unban_user, is_banned,
    disable_broadcast_for_user, enable_broadcast,
    is_broadcast_disabled, set_welcome_message, get_welcome_message,
    log_user_data, get_user_channels
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Pyrogram Client
app = Client(
    "approver_bot",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN,
)

LOG_CHANNEL = cfg.LOG_CHANNEL
FORCE_SUB_CHANNEL = cfg.FORCE_SUB_CHANNEL  # Without '@'

# Check Subscription
async def is_user_subscribed(client: Client, user_id: int, channel_username: str) -> bool:
    try:
        user = await client.get_chat_member(channel_username, user_id)
        return user.status in ["member", "administrator", "creator"]
    except errors.UserNotParticipant:
        return False
    except errors.ChatAdminRequired:
        logger.warning(f"Bot lacks admin rights in {channel_username}.")
        return False
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False


# /start Command
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    # Force Subscription Check
    if not await is_user_subscribed(app, m.from_user.id, FORCE_SUB_CHANNEL):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")]
        ])
        await m.reply(
            f"🔒 You must join [this channel](https://t.me/{FORCE_SUB_CHANNEL}) to use this bot!",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return

    # Banned User Check
    if is_banned(m.from_user.id):
        await m.reply("🚫 You are banned from using this bot!")
        return

    # Add User
    add_user(m.from_user.id, m.from_user.username)
    log_user_data(m.from_user.id, m.from_user.username, LOG_CHANNEL)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Channel", url="https://t.me/World_Fastest_Bots"),
            InlineKeyboardButton("Support", url="https://t.me/Fastest_Bots_Support"),
        ]
    ])
    await m.reply_photo(
        "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
        caption="Welcome to the fastest bot! Add me to your channels and groups.",
        reply_markup=keyboard,
    )


# /ban Command
@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/ban user_id`")
        return
    user_id = int(m.command[1])
    ban_user(user_id)
    disable_broadcast_for_user(user_id)
    await m.reply(f"🚫 User `{user_id}` has been banned.")


# /unban Command
@app.on_message(filters.command("unban") & filters.user(cfg.SUDO))
async def unban_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/unban user_id`")
        return
    user_id = int(m.command[1])
    unban_user(user_id)
    await m.reply(f"✅ User `{user_id}` has been unbanned.")


# /show_banned_users Command
@app.on_message(filters.command("show_banned_users") & filters.user(cfg.SUDO))
async def show_banned_users(_, m: Message):
    banned_users = all_banned_users()
    if not banned_users:
        await m.reply("🚫 No banned users found.")
        return
    text = "\n".join([f"• `{user['user_id']}`" for user in banned_users])
    await m.reply(f"📜 **Banned Users:**\n\n{text}")


# /disable_broadcast Command
@app.on_message(filters.command("disable_broadcast") & filters.user(cfg.SUDO))
async def disable_broadcast(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/disable_broadcast user_id`")
        return
    user_id = int(m.command[1])
    disable_broadcast_for_user(user_id)
    await m.reply(f"🚫 Broadcast disabled for user `{user_id}`.")


# /enable_broadcast Command
@app.on_message(filters.command("enable_broadcast") & filters.user(cfg.SUDO))
async def enable_broadcast(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/enable_broadcast user_id`")
        return
    user_id = int(m.command[1])
    enable_broadcast(user_id)
    await m.reply(f"✅ Broadcast enabled for user `{user_id}`.")


# /show_disable_broadcast_users Command
@app.on_message(filters.command("show_disable_broadcast_users") & filters.user(cfg.SUDO))
async def show_disabled_broadcast_users(_, m: Message):
    disabled_users = all_disabled_broadcast_users()
    if not disabled_users:
        await m.reply("🚫 No disabled broadcast users found.")
        return
    text = "\n".join([f"• `{user['user_id']}`" for user in disabled_users])
    await m.reply(f"📜 **Disabled Broadcast Users:**\n\n{text}")


# /user_channels Command
@app.on_message(filters.command("user_channels") & filters.user(cfg.SUDO))
async def user_channels(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/user_channels user_id`")
        return
    user_id = int(m.command[1])
    channels = get_user_channels(user_id)
    if not channels:
        await m.reply(f"🚫 No channels found for user `{user_id}`.")
        return
    text = "\n".join([f"• `{c['chat_id']}`: {c['chat_name']}" for c in channels])
    await m.reply(f"📜 **User Channels:**\n\n{text}")


# /stats Command
@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    active_users = len(all_users())
    await m.reply(f"📊 **Active Users:** `{active_users}`")


# Run the Bot
logger.info("🚀 Bot is live and running!")
app.run()
