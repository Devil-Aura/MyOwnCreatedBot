import logging
import asyncio
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.flood_420 import FloodWait
from database import (
    add_user, add_group, all_users, all_groups,
    remove_user, ban_user, unban_user, is_banned,
    disable_broadcast_for_user, is_broadcast_disabled,
    set_welcome_message, get_welcome_message,
    log_user_data, get_user_channels
)
from config import cfg

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Pyrogram Client
app = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN,
)

LOG_CHANNEL = cfg.LOG_CHANNEL

# Start Command
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    if is_banned(m.from_user.id):
        await m.reply("🚫 You are banned from using this bot!")
        return

    add_user(m.from_user.id, m.from_user.username)
    log_user_data(m.from_user.id, m.from_user.username, LOG_CHANNEL)

    await app.send_message(
        LOG_CHANNEL,
        f"🆕 **New User Alert!**\n"
        f"**Username:** @{m.from_user.username or 'N/A'}\n"
        f"**User ID:** `{m.from_user.id}`",
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗯 Channel", url="https://t.me/World_Fastest_Bots"),
            InlineKeyboardButton("💬 Support", url="https://t.me/Fastest_Bots_Support"),
        ],
        [
            InlineKeyboardButton("➕ Add Me in Channel", url="https://t.me/Request_acceept_bot?startchannel"),
            InlineKeyboardButton("➕ Add Me in Group", url="https://t.me/Auto_Request_Accept_Fast_bot?startgroup"),
        ],
    ])
    await m.reply_photo(
        "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
        caption=(
             f"**🙋🏻‍♂️Hello {m.from_user.mention}!\n"
            f"🚀 I am the FASTEST BOT, faster than light ⚡!"
            f" I approve join requests in just 0.5 seconds.\n\n"
            f" <blockquote> I'm an auto-approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            f"I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</blockquote>\n\n"
            f"Powered By : @World_Fastest_Bots**"
       ),
        reply_markup=keyboard,
    )

# Stats Command
@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    active_users = len(all_users())
    banned_users = users.count_documents({"banned": True})
    disabled_broadcast_users = len([user for user in all_users() if is_broadcast_disabled(user["user_id"])])
    await m.reply_text(
        f"📊 **Bot Statistics:**\n\n"
        f"👤 **Active Users:** `{active_users}`\n"
        f"🚫 **Banned Users:** `{banned_users}`\n"
        f"🔕 **Disabled Broadcast Users:** `{disabled_broadcast_users}`"
    )

# Set Welcome Message Command
@app.on_message(filters.command("set_welcome_msg") & filters.user(cfg.SUDO))
async def set_welcome_msg(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/set_welcome_msg <message>`")
        return

    message = " ".join(m.command[1:])
    set_welcome_message(m.chat.id, message)
    await m.reply(f"✅ Welcome message set to: {message}")

# User Channels Command
@app.on_message(filters.command("user_channels") & filters.user(cfg.SUDO))
async def user_channels(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/user_channels user_id`")
        return

    try:
        user_id = int(m.command[1])
        channels = get_user_channels(user_id)
        if not channels:
            await m.reply(f"🚫 No channels/groups found for user `{user_id}`.")
            return

        text = "\n".join([f"• `{c['chat_id']}`: {c['chat_name']} ({c['chat_url']})" for c in channels])
        await m.reply_text(f"📚 **Channels/Groups for User `{user_id}`:**\n\n{text}")
    except ValueError:
        await m.reply("❌ Invalid user ID. Please provide a numeric value.")

# Disable Broadcast Command
@app.on_message(filters.command("disable_broadcast") & filters.user(cfg.SUDO))
async def disable_broadcast(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/disable_broadcast user_id`")
        return

    try:
        user_id = int(m.command[1])
        disable_broadcast_for_user(user_id)
        await m.reply(f"🚫 Broadcast disabled for user `{user_id}`.")
    except ValueError:
        await m.reply("❌ Invalid user ID. Please provide a numeric value.")

# Enable Broadcast Command
@app.on_message(filters.command("enable_broadcast") & filters.user(cfg.SUDO))
async def enable_broadcast(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/enable_broadcast user_id`")
        return

    try:
        user_id = int(m.command[1])
        enable_broadcast(user_id)
        await m.reply(f"✅ Broadcast enabled for user `{user_id}`.")
    except ValueError:
        await m.reply("❌ Invalid user ID. Please provide a numeric value.")

# Show Disabled Broadcast Users Command
@app.on_message(filters.command("show_disable_broadcast_users") & filters.user(cfg.SUDO))
async def show_disabled_broadcast_users(_, m: Message):
    disabled_users = [user for user in all_users() if is_broadcast_disabled(user["user_id"])]
    if not disabled_users:
        await m.reply("🚫 No users have disabled broadcast.")
        return
    text = "\n".join([f"• User ID: `{user['user_id']}`" for user in disabled_users])
    await m.reply(f"📜 **Users with Disabled Broadcast:**\n\n{text}")

# Ban User Command
@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban_user_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/ban user_id`")
        return

    try:
        user_id = int(m.command[1])
        ban_user(user_id)
        disable_broadcast_for_user(user_id)
        await m.reply(f"🚫 User `{user_id}` has been banned from using this bot and their broadcast has been disabled.")
    except ValueError:
        await m.reply("❌ Invalid user ID. Please provide a numeric value.")

# Unban User Command
@app.on_message(filters.command("unban") & filters.user(cfg.SUDO))
async def unban_user_command(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/unban user_id`")
        return

    try:
        user_id = int(m.command[1])
        unban_user(user_id)
        await m.reply(f"✅ User `{user_id}` has been unbanned.")
    except ValueError:
        await m.reply("❌ Invalid user ID. Please provide a numeric value.")

# Show Banned Users Command
@app.on_message(filters.command("show_banned_users") & filters.user(cfg.SUDO))
async def show_banned_users(_, m: Message):
    banned_users = [user for user in all_users() if is_banned(user["user_id"])]
    if not banned_users:
        await m.reply("🚫 No banned users.")
        return
    text = "\n".join([f"• User ID: `{user['user_id']}`" for user in banned_users])
    await m.reply(f"📜 **Banned Users:**\n\n{text}")

# Run the Bot
logger.info("🚀 Bot is alive and running faster than light!")
app.run()
