import logging
from pyrogram import Client, filters, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import cfg
from database import (
    add_user, log_user_data, is_banned, all_users, disable_broadcast_for_user,
    is_broadcast_disabled, set_welcome_message, get_user_channels
)

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
FORCE_SUB_CHANNEL = cfg.FORCE_SUB_CHANNEL  # Add channel username in config.py without '@'


# Function to check if user is subscribed
async def is_user_subscribed(client: Client, user_id: int, channel_username: str) -> bool:
    try:
        user = await client.get_chat_member(channel_username, user_id)
        return user.status in ["member", "administrator", "creator"]
    except errors.UserNotParticipant:
        return False
    except errors.ChatAdminRequired:
        logger.warning(f"Bot is not an admin in the channel: {channel_username}")
        return False
    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return False


# Start Command
@app.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    # Check force subscription
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

    # Check if user is banned
    if is_banned(m.from_user.id):
        await m.reply("🚫 You are banned from using this bot!")
        return

    # Add user and log data
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
            f"**🙋🏻‍♂️ Hello {m.from_user.mention}!\n\n"
            f"🚀 I am the FASTEST BOT, faster than light ⚡!\n"
            f"I approve join requests in just 0.5 seconds.\n"
            f" <blockquote> I'm an auto-approve [Admin Join Requests](https://t.me/telegram/153) Bot.\n"
            f"I can approve users in Groups/Channels. Add me to your chat and promote me to admin with 'Add Members' permission.</blockquote>\n\n"
            f"Powered By : @World_Fastest_Bots**"
        ),
        reply_markup=keyboard,
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


# Stats Command
@app.on_message(filters.command("stats") & filters.user(cfg.SUDO))
async def stats(_, m: Message):
    active_users = len(all_users())
    await m.reply_text(f"📊 **Bot Statistics:**\n\n👤 **Active Users:** `{active_users}`")


# Run the Bot
logger.info("🚀 Bot is alive and running faster than light!")
app.run()
