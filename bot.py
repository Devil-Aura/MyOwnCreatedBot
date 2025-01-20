import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import cfg
from database import (
    all_users, remove_user, log_user_data, is_banned, add_user, 
    ban_user, unban_user, all_banned_users, disable_broadcast_for_user,
    enable_broadcast, all_disabled_broadcast_users, set_welcome_message,
    get_welcome_message, get_user_channels
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Pyrogram Client
app = Client(
    "broadcast_bot",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN,
)

LOG_CHANNEL = cfg.LOG_CHANNEL
FORCE_SUB_CHANNEL = cfg.FORCE_SUB_CHANNEL  # Add the channel username in config.py without '@'

# Function to check if a user is subscribed to the force-sub channel
async def is_user_subscribed(client: Client, user_id: int, channel_username: str) -> bool:
    try:
        user = await client.get_chat_member(channel_username, user_id)
        return user.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Subscription check failed: {e}")
        return False

# Start Command
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    if not await is_user_subscribed(app, m.from_user.id, FORCE_SUB_CHANNEL):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel", url=f"https://t.me/{FORCE_SUB_CHANNEL}")],
        ])
        await m.reply(
            f"🔒 You must join [this channel](https://t.me/{FORCE_SUB_CHANNEL}) to use this bot!",
            disable_web_page_preview=True,
            reply_markup=keyboard,
        )
        return

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
            InlineKeyboardButton("➕ Add Me in Channel", url="https://t.me/Auto_Request_Accept_Fast_bot?startchannel"),
            InlineKeyboardButton("➕ Add Me in Group", url="https://t.me/Auto_Request_Accept_Fast_bot?startgroup"),
        ],
    ])
    await m.reply_photo(
        "https://i.ibb.co/6wQZY57/photo-2024-12-30-17-57-41-7454266052625563676.jpg",
        caption=(
            f"**🙋🏻‍♂️ Hello {m.from_user.mention}!\n\n"
            f"🚀 I am the FASTEST BOT, faster than light ⚡!"
            f"I approve join requests in just 0.5 seconds.\n"
            f"<blockquote> I'm an auto-approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            f"I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</blockquote>\n\n"
            f"Powered By : @World_Fastest_Bots**"
        ),
        reply_markup=keyboard,
    )

# Broadcast Command
@app.on_message(filters.command("broadcast") & filters.user(cfg.SUDO))
async def broadcast(_, m: Message):
    if not m.reply_to_message:
        await m.reply("Reply to a message to broadcast it.")
        return

    users = all_users()
    sent, failed = 0, 0

    for user in users:
        try:
            await app.copy_message(
                chat_id=user["user_id"],
                from_chat_id=m.chat.id,
                message_id=m.reply_to_message.id
            )
            sent += 1
        except Exception as e:
            failed += 1
            if "user is deleted" in str(e).lower():
                remove_user(user["user_id"])

    await m.reply(f"📢 Broadcast completed!\n✅ Sent: {sent}\n❌ Failed: {failed}")

# Ban Command
@app.on_message(filters.command("ban") & filters.user(cfg.SUDO))
async def ban(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/ban user_id`")
        return
    user_id = int(m.command[1])
    ban_user(user_id)
    disable_broadcast_for_user(user_id)
    await m.reply(f"🚫 User `{user_id}` has been banned.")

# Unban Command
@app.on_message(filters.command("unban") & filters.user(cfg.SUDO))
async def unban(_, m: Message):
    if len(m.command) < 2:
        await m.reply("Usage: `/unban user_id`")
        return
    user_id = int(m.command[1])
    unban_user(user_id)
    await m.reply(f"✅ User `{user_id}` has been unbanned.")

# Show Banned Users Command
@app.on_message(filters.command("show_banned_users") & filters.user(cfg.SUDO))
async def show_banned_users(_, m: Message):
    users = all_banned_users()
    if not users:
        await m.reply("🚫 No banned users found.")
        return
    text = "\n".join([f"• `{u['user_id']}`" for u in users])
    await m.reply(f"📜 **Banned Users:**\n\n{text}")

# Stats Command
@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    total_users = len(all_users())
    await m.reply(f"📊 **Total Active Users:** `{total_users}`")

# Run the Bot
logger.info("🚀 Bot is alive and running!")
app.run()
